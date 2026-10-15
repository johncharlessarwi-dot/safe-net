"""Outgoing SMS through NextSMS (https://nextsms.co.tz). Standard library only."""
import base64
import json
import logging
import threading
import urllib.error
import urllib.request

from config import Config

log = logging.getLogger('safenet.sms')


def is_configured():
    return bool(Config.NEXTSMS_USERNAME and Config.NEXTSMS_PASSWORD and Config.NEXTSMS_SENDER_ID)


def send_sms(to, text, reference=None):
    """Send now; returns True on success. `to` is 255XXXXXXXXX."""
    if not is_configured() or not to:
        log.info('SMS not sent (not configured or no number): %s', text[:60])
        return False
    auth = base64.b64encode(f'{Config.NEXTSMS_USERNAME}:{Config.NEXTSMS_PASSWORD}'.encode()).decode()
    body = {'from': Config.NEXTSMS_SENDER_ID, 'to': to, 'text': text[:640]}
    if reference:
        body['reference'] = reference[:64]
    req = urllib.request.Request(Config.NEXTSMS_URL, data=json.dumps(body).encode(), method='POST', headers={
        'Authorization': f'Basic {auth}', 'Content-Type': 'application/json', 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            ok = 200 <= resp.status < 300
            log.info('SMS to %s: HTTP %s %s', to, resp.status, resp.read(200).decode('utf-8', 'replace'))
            return ok
    except urllib.error.HTTPError as e:
        log.warning('SMS to %s failed: HTTP %s %s', to, e.code, e.read(200).decode('utf-8', 'replace'))
    except (urllib.error.URLError, TimeoutError) as e:
        log.warning('SMS to %s failed: %s', to, e)
    return False


def send_sms_async(to, text, reference=None):
    """Fire and forget, so a slow SMS gateway never delays a web request."""
    if is_configured() and to:
        threading.Thread(target=send_sms, args=(to, text, reference), daemon=True).start()
