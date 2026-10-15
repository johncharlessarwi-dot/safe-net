"""TP-Link Omada Controller client for the External Portal Server flow.

How it works with SafeNet:
  1. The Omada Controller sends unauthenticated guests to SafeNet's login page
     (/omada/<site token>) with clientMac, apMac, ssidName, radioId, site, redirectUrl
     (or gatewayMac and vid when an Omada gateway runs the portal).
  2. The guest enters a voucher or pays with mobile money on SafeNet's page.
  3. SafeNet logs in to the controller as a hotspot operator and calls
     extPortal/auth, which lets the guest online for the paid time.

Written against the Omada SDN Controller v5 External Portal API:
  GET  /api/info                                -> result.omadacId
  POST /{omadacId}/api/v2/hotspot/login         {"name", "password"} -> result.token + session cookie
  POST /{omadacId}/api/v2/hotspot/extPortal/auth  (header Csrf-Token) -> errorCode 0
Controllers usually have a self-signed certificate, so TLS checking is optional.
"""
import http.cookiejar
import ipaddress
import socket
import json
import re
import ssl
import urllib.error
import urllib.request


class OmadaError(Exception):
    pass


AUTH_TYPE_EXTERNAL_PORTAL = '4'
MAX_SECONDS = 30 * 86400


def public_address_problem(url):
    """Why SafeNet must not connect to this address (a tenant's controller has to be on the internet), or None.
    Stops a tenant from using SafeNet to reach the server itself or private networks."""
    from urllib.parse import urlparse
    parsed = urlparse(url or '')
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        return 'Enter the controller address, e.g. https://203.0.113.5:8043'
    try:
        infos = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == 'https' else 80), proto=socket.IPPROTO_TCP)
    except (socket.gaierror, UnicodeError, ValueError):
        return f"can't find the address {parsed.hostname}"
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global or ip.is_multicast:
            return 'the controller must have a public internet address (not a local or private one)'
    return None


# A business's own login to SafeNet's controller ("advanced" users): only its own sites, and view-only for the
# settings SafeNet manages (network, hotspot/portal), so the guest login page can't be broken by accident.
BUSINESS_ROLE = 'SafeNet business'
_BLOCK, _VIEW, _MODIFY = 0, 1, 2
BUSINESS_PRIVILEGE = {
    # controller-wide: nothing
    'license': _BLOCK, 'globalDashboard': _BLOCK, 'globalLog': _BLOCK, 'licenseBind': _BLOCK, 'users': _BLOCK, 'roles': _BLOCK,
    'samlUsers': _BLOCK, 'samlRoles': _BLOCK, 'samlSsos': _BLOCK, 'globalSetting': _BLOCK, 'globalExportData': _BLOCK,
    'exportGlobalLog': _BLOCK, 'globalCluster': _BLOCK, 'anomaly': _BLOCK, 'analyze': _BLOCK, 'globalSecurity': _BLOCK,
    'globalWebhook': _BLOCK, 'globalMapToken': _BLOCK, 'siteTemplate': _BLOCK, 'firmwareManager': _BLOCK, 'sdWan': _BLOCK,
    # their own site
    'siteHome': _VIEW, 'dashboard': _VIEW, 'statics': _VIEW, 'insight': _VIEW, 'report': _VIEW, 'log': _VIEW, 'siteAnalyze': _VIEW,
    'devices': _MODIFY, 'adopt': _MODIFY, 'addDevices': _MODIFY, 'addAdoptDevice': _MODIFY, 'manualUpgrade': _MODIFY,
    'clients': _MODIFY, 'map': _MODIFY, 'exportData': _MODIFY,
    'network': _VIEW, 'hotspot': _VIEW, 'deviceAccount': _BLOCK, 'deviceRecovery': _BLOCK,
}


def business_password(length=16):
    """A password the controller accepts: upper, lower, digit and symbol (no quote, space or '?')."""
    import secrets
    groups = ('ABCDEFGHJKLMNPQRSTUVWXYZ', 'abcdefghijkmnopqrstuvwxyz', '23456789', '!#$%&*@^')
    chars = [secrets.choice(g) for g in groups] + [secrets.choice(''.join(groups)) for _ in range(length - 4)]
    secrets.SystemRandom().shuffle(chars)
    return ''.join(chars)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, 'redirects are not followed', headers, fp)


class Controller:
    def __init__(self, url, username, password, verify_tls=False, timeout=10, public_only=False):
        """public_only: a tenant's own controller (must be on the internet); SafeNet's hosted one is internal."""
        self.base = (url or '').rstrip('/')
        self.public_only = public_only
        self.username = username or ''
        self.password = password or ''
        self.timeout = timeout
        context = ssl.create_default_context()
        if not verify_tls:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        handlers = [urllib.request.HTTPSHandler(context=context), urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())]
        if public_only:
            handlers.append(_NoRedirect())
        self.opener = urllib.request.build_opener(*handlers)
        self._cid = None
        self._token = None

    def _request(self, method, path, body=None, token=None):
        if self.public_only:
            problem = public_address_problem(self.base)      # checked every time (DNS can change)
            if problem:
                raise OmadaError(problem)
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method)
        req.add_header('Accept', 'application/json')
        if data is not None:
            req.add_header('Content-Type', 'application/json')
        if token:
            req.add_header('Csrf-Token', token)
        try:
            with self.opener.open(req, timeout=self.timeout) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as e:
            raise OmadaError(f'controller answered HTTP {e.code} for {path}') from e
        except (urllib.error.URLError, OSError) as e:
            reason = getattr(e, 'reason', e)
            raise OmadaError(f"can't reach the controller at {self.base} ({reason})") from e
        try:
            reply = json.loads(raw or b'{}')
        except ValueError as e:
            raise OmadaError(f'controller sent something that is not JSON for {path}') from e
        if reply.get('errorCode', 0) != 0:
            raise OmadaError(f"controller refused {path}: {reply.get('msg') or reply.get('errorCode')}")
        return reply.get('result') or {}

    def controller_id(self):
        if self._cid is None:
            self._cid = str(self._request('GET', '/api/info').get('omadacId') or '')
        return self._cid

    def _prefix(self):
        cid = self.controller_id()
        return f'/{cid}' if cid else ''

    def login(self):
        result = self._request('POST', f'{self._prefix()}/api/v2/hotspot/login',
                               {'name': self.username, 'password': self.password})
        self._token = result.get('token')
        if not self._token:
            raise OmadaError('controller login gave no token: check the hotspot operator name and password')
        return self._token

    def authorize(self, client_mac, seconds, *, site, ap_mac=None, ssid=None, radio_id=None,
                  gateway_mac=None, vid=None):
        """Let a guest online for `seconds`. EAP portals send apMac/ssidName/radioId;
        gateway portals send gatewayMac/vid."""
        if not client_mac or not site:
            raise OmadaError('the login page was opened without the Omada details (clientMac/site)')
        seconds = max(60, min(int(seconds), MAX_SECONDS))
        body = {'clientMac': client_mac, 'site': site, 'time': str(seconds * 1_000_000),
                'authType': AUTH_TYPE_EXTERNAL_PORTAL}
        if ap_mac:
            body.update(apMac=ap_mac, ssidName=ssid or '', radioId=str(radio_id if radio_id is not None else '0'))
        else:
            body.update(gatewayMac=gateway_mac or '', vid=str(vid or ''))
        token = self._token or self.login()
        try:
            return self._request('POST', f'{self._prefix()}/api/v2/hotspot/extPortal/auth', body, token=token)
        except OmadaError:
            # The operator session may have expired: log in again once
            token = self.login()
            return self._request('POST', f'{self._prefix()}/api/v2/hotspot/extPortal/auth', body, token=token)

    def check(self):
        """Connect and log in; returns the controller id (empty for older controllers)."""
        cid = self.controller_id()
        self.login()
        return cid


def device_password(length=18):
    """A password Omada accepts for device accounts: 10-64 characters with upper and lower case,
    digits and a symbol, and no character twice in a row."""
    import secrets, string
    pools = (string.ascii_uppercase, string.ascii_lowercase, string.digits, '#@%&*')
    while True:
        chars = [secrets.choice(pool) for pool in pools] + [secrets.choice(''.join(pools)) for _ in range(length - 4)]
        secrets.SystemRandom().shuffle(chars)
        pw = ''.join(chars)
        if not any(pw[i] == pw[i + 1] for i in range(len(pw) - 1)):
            return pw


class OpenApi:
    """Omada Open API (client-credentials app) used to set sites up for tenants:
    create the site, adopt access points, create the guest Wi-Fi and the portal
    that sends guests to SafeNet, and cut guests off."""

    def __init__(self, url, client_id, client_secret, verify_tls=False, timeout=15):
        self.web = Controller(url, '', '', verify_tls=verify_tls, timeout=timeout)
        self.client_id, self.client_secret = client_id or '', client_secret or ''
        self._token, self._token_until = None, 0

    # -- plumbing --------------------------------------------------------
    def _cid(self):
        cid = self.web.controller_id()
        if not cid:
            raise OmadaError('the controller did not report its ID')
        return cid

    def _authorize(self):
        import time as _time
        if self._token and _time.time() < self._token_until:
            return self._token
        result = self.web._request('POST', '/openapi/authorize/token?grant_type=client_credentials',
                                   {'omadacId': self._cid(), 'client_id': self.client_id, 'client_secret': self.client_secret})
        token = result.get('accessToken')
        if not token:
            raise OmadaError('the controller gave no access token: check the Open API app in the controller')
        self._token, self._token_until = token, _time.time() + max(60, int(result.get('expiresIn') or 3600) - 60)
        return token

    def _call(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        url = f'{self.web.base}/openapi/v1/{self._cid()}{path}' if not path.startswith('/openapi/') else self.web.base + path.replace('{cid}', self._cid())
        for attempt in (1, 2):
            req = urllib.request.Request(url, data=data, method=method)
            req.add_header('Accept', 'application/json')
            req.add_header('Content-Type', 'application/json')
            req.add_header('Authorization', f'AccessToken={self._authorize()}')
            try:
                with self.web.opener.open(req, timeout=self.web.timeout) as resp:
                    reply = json.loads(resp.read() or b'{}')
            except urllib.error.HTTPError as e:
                raise OmadaError(f'controller answered HTTP {e.code} for {path}') from e
            except (urllib.error.URLError, OSError) as e:
                raise OmadaError(f"can't reach the controller ({getattr(e, 'reason', e)})") from e
            except ValueError as e:
                raise OmadaError(f'controller sent something that is not JSON for {path}') from e
            code = reply.get('errorCode', 0)
            if code in (-44106, -44112, -44113) and attempt == 1:     # token expired or invalid: get a new one
                self._token = None
                continue
            if code != 0:
                raise OmadaError(f"controller refused {path}: {reply.get('msg') or code}")
            return reply.get('result')
        raise OmadaError('controller kept refusing the access token')

    @staticmethod
    def mac(value):
        raw = re.sub(r'[^0-9A-Fa-f]', '', value or '').upper()
        if len(raw) != 12:
            raise OmadaError('enter the MAC address from the label, e.g. B8-FB-B3-79-C7-E6')
        return '-'.join(raw[i:i + 2] for i in range(0, 12, 2))

    def _pages(self, path, key='data'):
        result = self._call('GET', f'{path}{"&" if "?" in path else "?"}page=1&pageSize=1000') or {}
        return result.get(key, []) if isinstance(result, dict) else result

    # -- a business's own controller login -------------------------------
    def ensure_business_role(self):
        """The 'SafeNet business' role's id (created the first time)."""
        roles = self._call('GET', '/roles') or []
        if isinstance(roles, dict):
            roles = roles.get('data') or []
        for role in roles:
            if role.get('name') == BUSINESS_ROLE:
                return role['id']
        return (self._call('POST', '/roles', {'name': BUSINESS_ROLE, 'privilege': BUSINESS_PRIVILEGE}) or {})['roleId']

    def create_business_user(self, name, password, role_id, site_ids):
        result = self._call('POST', '/users', {'type': 0, 'name': name, 'password': password, 'roleId': role_id,
                                               'allSite': False, 'sites': list(site_ids)}) or {}
        return result.get('userId')

    def update_business_user(self, user_id, name, role_id, site_ids, password=None):
        body = {'name': name, 'roleId': role_id, 'allSite': False, 'sites': list(site_ids)}
        if password:
            body['password'] = password
        self._call('PUT', f'/users/{user_id}', body)

    # -- clients ---------------------------------------------------------
    def clients(self, site_id):
        """Phones the site's access points see now: mac, ip, trafficDown/trafficUp (bytes), uptime (s), active."""
        return self._pages(f'/sites/{site_id}/clients')

    # -- sites -----------------------------------------------------------
    def find_site(self, name):
        for s in self._pages('/sites?searchKey=' + urllib.request.quote(name)):
            if (s.get('name') or '').strip().lower() == name.strip().lower():
                return s.get('siteId')
        return None

    def create_site(self, name, device_user, device_password, region='Tanzania', time_zone='Africa/Nairobi'):
        scenarios = self._call('GET', '/scenarios') or []
        scenario = 'Hotel' if 'Hotel' in scenarios else (scenarios[0] if scenarios else 'Hotel')
        result = self._call('POST', '/sites', {'name': name[:64], 'type': 0, 'region': region, 'timeZone': time_zone,
                                              'scenario': scenario, 'supportES': False, 'supportL2': True,
                                              'deviceAccountSetting': {'username': device_user, 'password': device_password}}) or {}
        return result.get('siteId') or self.find_site(name[:64])

    # -- devices ---------------------------------------------------------
    # detailStatus 20-27: pending, adopting or adopt-failed (the device list includes them, for every site)
    NOT_YET_ADOPTED = {20, 21, 22, 23, 24, 25, 26, 27}

    def devices(self, site_id):
        """Access points adopted into this site (the controller also lists devices waiting to be adopted)."""
        return [d for d in self._pages(f'/sites/{site_id}/devices')
                if d.get('status') != 2 and d.get('detailStatus') not in self.NOT_YET_ADOPTED]

    def pending(self, site_id):
        return self._pages(f'/sites/{site_id}/grid/devices/pending')

    def adopt(self, site_id, mac, username=None, password=None):
        body = {'username': username, 'password': password} if username and password else {}
        self._call('POST', f'/sites/{site_id}/devices/{mac}/start-adopt', body)

    def adopt_result(self, site_id, mac):
        return self._call('GET', f'/sites/{site_id}/devices/{mac}/adopt-result') or {}

    # -- guest Wi-Fi and portal --------------------------------------------
    def ensure_ssid(self, site_id, name):
        groups = self._call('GET', f'/sites/{site_id}/wireless-network/ssids?type=1') or []
        for g in groups:
            for s in g.get('ssidList') or []:
                if s.get('ssidName') == name:
                    return s.get('ssidId')
        wlans = self._call('GET', f'/sites/{site_id}/wireless-network/wlans') or []
        wlan = next((w for w in wlans if w.get('primary')), wlans[0] if wlans else None)
        if not wlan:
            raise OmadaError('the site has no WLAN group')
        self._call('POST', f'/openapi/v2/{{cid}}/sites/{site_id}/wireless-network/wlans/{wlan["wlanId"]}/ssids',
                   {'name': name[:32], 'deviceType': 1, 'band': 3, 'guestNetEnable': True, 'security': 0, 'broadcast': True})
        for g in self._call('GET', f'/sites/{site_id}/wireless-network/ssids?type=1') or []:
            for s in g.get('ssidList') or []:
                if s.get('ssidName') == name[:32]:
                    return s.get('ssidId')
        raise OmadaError('the Wi-Fi was not created')

    def ensure_portal(self, site_id, ssid_id, portal_url, name='SafeNet'):
        scheme, _, rest = portal_url.partition('://')
        body = {'name': name, 'enable': True, 'ssidList': [ssid_id], 'authType': 4,
                'authTimeout': {'customTimeout': 1, 'customTimeoutUnit': 3},
                'httpsRedirectEnable': False, 'landingPage': 1,
                'externalPortal': {'hostType': 2, 'serverUrlScheme': scheme or 'https', 'serverUrl': rest},
                # required even though guests see SafeNet's page, not Omada's
                'portalCustomize': {'defaultLanguage': 1, 'logoDisplay': False, 'welcomeEnable': False,
                                    'termsOfServiceEnable': False, 'copyrightEnable': False}}
        portals = self._call('GET', f'/sites/{site_id}/portals') or []
        # reuse our portal, or one already attached to this Wi-Fi (e.g. set up by hand), never add a second
        existing = next((p for p in portals if p.get('name') == name), None) or \
            next((p for p in portals if ssid_id in (p.get('ssidList') or [])), None)
        if existing:
            ssids = sorted(set((existing.get('ssidList') or []) + [ssid_id]))
            self._call('PATCH', f'/sites/{site_id}/portal/{existing["id"]}', {**body, 'name': existing.get('name') or name, 'ssidList': ssids})
            return existing['id']
        self._call('POST', f'/sites/{site_id}/portal', body)
        return next((p.get('id') for p in (self._call('GET', f'/sites/{site_id}/portals') or []) if p.get('name') == name), None)

    def ensure_pre_auth(self, site_id, host):
        current = self._call('GET', f'/sites/{site_id}/setting/access-control') or {}
        policies = current.get('preAuthAccessPolicies') or []
        if not any(p.get('type') == 2 and p.get('url') == host for p in policies):
            policies = policies + [{'type': 2, 'url': host}]
        self._call('PATCH', f'/sites/{site_id}/setting/access-control',
                   {'preAuthAccessEnable': True, 'preAuthAccessPolicies': policies,
                    'freeAuthClientEnable': bool(current.get('freeAuthClientEnable')),
                    'freeAuthClientPolicies': current.get('freeAuthClientPolicies') or []})

    def ensure_operator_site(self, site_id, operator, operator_password, any_site_id):
        """Give SafeNet's hotspot operator access to every site, including a new one. (The operator
        list does not report an operator's current sites, so always send the complete list.)"""
        ops = self._pages(f'/sites/{any_site_id}/hotspot/operators')
        op = next((o for o in ops if o.get('name') == operator), None)
        if op is None:
            return False
        sites = [s.get('siteId') for s in self._pages('/sites') if s.get('siteId')]
        if site_id not in sites:
            sites.append(site_id)
        self._call('PATCH', f'/sites/{any_site_id}/hotspot/operators/{op["id"]}',
                   {'name': operator, 'password': operator_password, 'operatorRoleType': op.get('operatorRoleType', 0),
                    'selectedSites': sites})
        return True

    @staticmethod
    def _rate(speed):
        """'5M' / '512k' / '1.5M' (bits per second) -> (unit, value) for Omada: unit 1 = Kbps, 2 = Mbps, value 1-1024."""
        m = re.match(r'^\s*(\d+(?:\.\d+)?)\s*([kKmMgG]?)', str(speed or ''))
        if not m:
            return None
        kbps = float(m.group(1)) * {'': 1000, 'k': 1, 'm': 1000, 'g': 1000000}[m.group(2).lower()]
        if kbps <= 0:
            return None
        if kbps <= 1024 and kbps % 1000:
            return 1, max(1, int(round(kbps)))
        return 2, max(1, min(1024, int(round(kbps / 1000))))

    def set_client_rate(self, site_id, client_mac, upload=None, download=None):
        """Limit one guest's speed (e.g. '5M' down, '2M' up), or remove the limit when both are empty."""
        up, down = self._rate(upload), self._rate(download)
        # mode 0 = custom speeds (1 = a saved profile); the controller wants units and limits even when off
        custom = {'enable': bool(up or down), 'upEnable': bool(up), 'upUnit': (up or (2, 1024))[0], 'upLimit': (up or (2, 1024))[1],
                  'downEnable': bool(down), 'downUnit': (down or (2, 1024))[0], 'downLimit': (down or (2, 1024))[1]}
        self._call('PATCH', f'/sites/{site_id}/clients/{self.mac(client_mac)}/ratelimit', {'mode': 0, 'customRateLimit': custom})

    def unauth(self, site_id, client_mac):
        self._call('POST', f'/sites/{site_id}/hotspot/clients/{self.mac(client_mac)}/unauth')


class OpenApiAdmin(OpenApi):
    """The same Open API, signed in as a controller administrator (authorization code mode). The controller only
    lets this mode manage its users, e.g. a business's own login. Flow: /openapi/authorize/login (username,
    password) -> /openapi/authorize/code (with that session) -> /openapi/authorize/token (code, app id and secret)."""

    def __init__(self, url, client_id, client_secret, username, password, verify_tls=False, timeout=15):
        super().__init__(url, client_id, client_secret, verify_tls=verify_tls, timeout=timeout)
        self.username, self.password = username or '', password or ''

    def _post(self, path, body=None, headers=None):
        req = urllib.request.Request(self.web.base + path, data=json.dumps(body or {}).encode(), method='POST')
        req.add_header('Content-Type', 'application/json')
        req.add_header('Accept', 'application/json')
        for key, value in (headers or {}).items():
            req.add_header(key, value)
        name = path.split('?')[0]
        try:
            with self.web.opener.open(req, timeout=self.web.timeout) as resp:
                reply = json.loads(resp.read() or b'{}')
        except urllib.error.HTTPError as e:
            raise OmadaError(f'controller answered HTTP {e.code} for {name}') from e
        except (urllib.error.URLError, OSError) as e:
            raise OmadaError(f"can't reach the controller ({getattr(e, 'reason', e)})") from e
        except ValueError as e:
            raise OmadaError(f'controller sent something that is not JSON for {name}') from e
        if reply.get('errorCode', 0) != 0:
            raise OmadaError(f"controller refused {name}: {reply.get('msg') or reply.get('errorCode')}")
        return reply.get('result')

    def _authorize(self):
        import time as _time
        from urllib.parse import quote
        if self._token and _time.time() < self._token_until:
            return self._token
        if not (self.username and self.password):
            raise OmadaError('no controller administrator login is set')
        query = f'client_id={quote(self.client_id)}&omadac_id={quote(self._cid())}'
        login = self._post(f'/openapi/authorize/login?{query}', {'username': self.username, 'password': self.password}) or {}
        code = self._post(f'/openapi/authorize/code?{query}&response_type=code', None,
                          {'Csrf-Token': str(login.get('csrfToken') or ''), 'Cookie': f"TPOMADA_SESSIONID={login.get('sessionId') or ''}"})
        if not code:
            raise OmadaError('the controller gave no authorization code')
        result = self._post(f'/openapi/authorize/token?grant_type=authorization_code&code={quote(str(code))}',
                            {'client_id': self.client_id, 'client_secret': self.client_secret}) or {}
        token = result.get('accessToken')
        if not token:
            raise OmadaError('the controller gave no access token for the administrator login')
        self._token, self._token_until = token, _time.time() + max(60, int(result.get('expiresIn') or 3600) - 60)
        return token

