"""Minimal ClickPesa collection client (USSD push). Standard library only.

Docs: https://docs.clickpesa.com (no sandbox - every call is live).
"""
import hashlib
import hmac
import json
import threading
import time
import urllib.error
import urllib.request
from collections import namedtuple

import safetext
from config import Config

# Whose ClickPesa account to use: the platform's (from .env) or a tenant's own
Credentials = namedtuple('Credentials', 'client_id api_key checksum_key')


def platform_credentials():
    return Credentials(Config.CLICKPESA_CLIENT_ID, Config.CLICKPESA_API_KEY, Config.CLICKPESA_CHECKSUM_KEY)


class ClickPesaError(Exception):
    """Message is cleaned of keys and IDs (ClickPesa echoes the client id in some errors)."""
    def __init__(self, message=''):
        super().__init__(safetext.clean(message))


_tokens = {}  # client_id -> (header value, expiry)
_token_lock = threading.Lock()


def is_configured(creds=None):
    creds = creds or platform_credentials()
    return bool(creds.client_id and creds.api_key)


def _request(method, path, body=None, headers=None, timeout=20):
    url = Config.CLICKPESA_BASE_URL.rstrip('/') + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        'Content-Type': 'application/json', 'Accept': 'application/json', **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read() or b'null')
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', 'replace')[:300]
        try:
            detail = json.loads(detail).get('message', detail)
        except (ValueError, AttributeError):
            pass
        raise ClickPesaError(f'{e.code}: {detail}') from None
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        raise ClickPesaError(f'ClickPesa unreachable: {e}') from None


def _auth_header(creds):
    """Tokens last 1 hour and already include the 'Bearer ' prefix."""
    with _token_lock:
        cached = _tokens.get(creds.client_id)
        if cached and time.time() < cached[1]:
            return cached[0]
        data = _request('POST', '/third-parties/generate-token', headers={
            'client-id': creds.client_id, 'api-key': creds.api_key})
        token = (data or {}).get('token')
        if not token:
            raise ClickPesaError('ClickPesa did not return a token')
        header = token if token.startswith('Bearer ') else f'Bearer {token}'
        _tokens[creds.client_id] = (header, time.time() + 55 * 60)
        return header


def test_credentials(creds):
    """Raises ClickPesaError if ClickPesa rejects these keys."""
    with _token_lock:
        _tokens.pop(creds.client_id, None)
    _auth_header(creds)


def _canonical(obj):
    if isinstance(obj, dict):
        return {k: _canonical(obj[k]) for k in sorted(obj)}
    if isinstance(obj, list):
        return [_canonical(v) for v in obj]
    return obj


def checksum(payload, key=None):
    """HMAC-SHA256 over the key-sorted compact JSON (checksum fields excluded)."""
    key = Config.CLICKPESA_CHECKSUM_KEY if key is None else key
    body = {k: v for k, v in payload.items() if k not in ('checksum', 'checksumMethod')}
    text = json.dumps(_canonical(body), separators=(',', ':'))
    return hmac.new(key.encode(), text.encode(), hashlib.sha256).hexdigest()


def _payment_payload(amount, phone, reference, creds):
    payload = {
        'amount': str(int(amount)) if float(amount).is_integer() else str(amount),
        'currency': 'TZS',
        'orderReference': reference,
        'phoneNumber': phone,
    }
    if creds.checksum_key:
        payload['checksum'] = checksum(payload, creds.checksum_key)
    return payload


def preview_ussd_push(amount, phone, reference, creds=None):
    """Checks the number and which mobile-money methods are up, without charging.
    Returns the list of available method names (e.g. ['M-PESA'])."""
    creds = creds or platform_credentials()
    data = _request('POST', '/third-parties/payments/preview-ussd-push-request',
                    _payment_payload(amount, phone, reference, creds),
                    headers={'Authorization': _auth_header(creds)}) or {}
    methods = data.get('activeMethods') or []
    return [m.get('name') for m in methods if (m.get('status') or '').upper() == 'AVAILABLE']


def initiate_ussd_push(amount, phone, reference, creds=None):
    """Sends the PIN prompt to the customer's phone. Returns ClickPesa's transaction."""
    creds = creds or platform_credentials()
    return _request('POST', '/third-parties/payments/initiate-ussd-push-request',
                    _payment_payload(amount, phone, reference, creds),
                    headers={'Authorization': _auth_header(creds)})


def query_payment(reference, creds=None):
    """Latest ClickPesa record for an order reference, or None if unknown."""
    creds = creds or platform_credentials()
    try:
        data = _request('GET', f'/third-parties/payments/{reference}',
                        headers={'Authorization': _auth_header(creds)})
    except ClickPesaError as e:
        if str(e).startswith('404'):
            return None
        raise
    if isinstance(data, list):
        if not data:
            return None
        paid = [r for r in data if r.get('status') in ('SUCCESS', 'SETTLED')]
        return paid[0] if paid else max(data, key=lambda r: r.get('updatedAt') or '')
    return data


# Payouts (disbursements) from the account's balance: to a mobile-money wallet or a Lipa Namba.
# ClickPesa allows one create request per merchant every 60 seconds.
PAYOUT_DONE = ('SUCCESS',)
PAYOUT_FAILED = ('FAILED', 'REFUNDED', 'REVERSED')


def _payout_payload(amount, reference, creds, phone=None, lipa_namba=None, provider_code=None):
    payload = {'amount': int(amount) if float(amount).is_integer() else float(amount),
               'currency': 'TZS', 'orderReference': reference}
    if lipa_namba:
        payload.update(lipaNamba=lipa_namba, providerCode=provider_code)
    else:
        payload['phoneNumber'] = phone
    if creds.checksum_key:
        payload['checksum'] = checksum(payload, creds.checksum_key)
    return payload


def _payout_path(action, lipa_namba):
    return f'/third-parties/payouts/{action}-' + ('lipa-namba-payout' if lipa_namba else 'mobile-money-payout')


def preview_payout(amount, reference, phone=None, lipa_namba=None, provider_code=None, creds=None):
    """Checks a payout without sending it: receiver name, fee and the account balance."""
    creds = creds or platform_credentials()
    return _request('POST', _payout_path('preview', lipa_namba),
                    _payout_payload(amount, reference, creds, phone, lipa_namba, provider_code),
                    headers={'Authorization': _auth_header(creds)}) or {}


def create_payout(amount, reference, phone=None, lipa_namba=None, provider_code=None, creds=None):
    """Sends the money. AUTHORIZED means accepted, not settled: poll query_payout."""
    creds = creds or platform_credentials()
    return _request('POST', _payout_path('create', lipa_namba),
                    _payout_payload(amount, reference, creds, phone, lipa_namba, provider_code),
                    headers={'Authorization': _auth_header(creds)}, timeout=40) or {}


def query_payout(reference, creds=None):
    """Latest record for a payout's order reference, or None if ClickPesa doesn't know it."""
    creds = creds or platform_credentials()
    try:
        data = _request('GET', f'/third-parties/payouts/{reference}', headers={'Authorization': _auth_header(creds)})
    except ClickPesaError as e:
        if str(e).startswith('404'):
            return None
        raise
    if isinstance(data, list):
        return max(data, key=lambda r: r.get('updatedAt') or '') if data else None
    return data


def lipa_namba_providers(creds=None):
    """[(name, providerCode)] that Lipa Namba payouts can go to."""
    creds = creds or platform_credentials()
    data = _request('GET', '/third-parties/payouts/lipa-namba-providers', headers={'Authorization': _auth_header(creds)}) or []
    return [(p.get('name', ''), str(p.get('providerCode', ''))) for p in data if p.get('providerCode')]
