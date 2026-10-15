"""Make payment-provider error text safe to store, log and show: no keys, tokens or account IDs.

Providers sometimes echo identifiers back (e.g. ClickPesa: "Application <client id> has no access to
PAYOUT API"). Every provider error goes through clean() before anyone can see it.
"""
import re

from config import Config

# Known provider messages, said plainly (and without the identifiers they carry)
FRIENDLY = (
    (re.compile(r'application\s+\S+\s+has no access to payout api', re.I),
     "payouts aren't switched on for SafeNet's ClickPesa app. In the ClickPesa dashboard, open the app and enable the Payout API."),
    (re.compile(r'no balance account is linked', re.I),
     'the account has no balance yet (it needs a first successful payment or deposit).'),
)

_PATTERNS = (
    re.compile(r'snp_[A-Za-z0-9]+'),                                   # Snippe API keys
    re.compile(r'Bearer\s+\S+', re.I),                                  # auth headers
    re.compile(r'eyJ[A-Za-z0-9_\-]+(?:\.[A-Za-z0-9_\-]+)*'),            # JWTs (ClickPesa tokens)
    re.compile(r'(?i)(application|app|client[ _-]?id|api[ _-]?key|key|token|secret)(\s*[:=]?\s*)[A-Za-z0-9_\-]{12,}'),
    re.compile(r'\b(?=[A-Za-z0-9_\-]*\d)(?=[A-Za-z0-9_\-]*[A-Za-z])[A-Za-z0-9_\-]{20,}\b'),   # long mixed IDs
)


def _secrets():
    values = (Config.CLICKPESA_CLIENT_ID, Config.CLICKPESA_API_KEY, Config.CLICKPESA_CHECKSUM_KEY,
              getattr(Config, 'SNIPPE_API_KEY', ''), getattr(Config, 'SNIPPE_WEBHOOK_KEY', ''),
              getattr(Config, 'NEXTSMS_PASSWORD', ''), getattr(Config, 'NEXTSMS_USERNAME', ''))
    return [v for v in values if v and len(v) >= 6]


def clean(text, extra_secrets=()):
    """`text` with secrets and identifiers replaced by [hidden], and known errors explained."""
    text = str(text or '')
    for pattern, plain in FRIENDLY:
        if pattern.search(text):
            code = re.match(r'\s*(\d{3}):', text)
            return (f'{code.group(1)}: ' if code else '') + plain
    for value in list(_secrets()) + [s for s in extra_secrets if s and len(s) >= 6]:
        text = text.replace(value, '[hidden]')
    for pattern in _PATTERNS:
        if pattern.groups >= 2:
            text = pattern.sub(lambda m: f'{m.group(1)}{m.group(2)}[hidden]', text)
        else:
            text = pattern.sub('[hidden]', text)
    return text
