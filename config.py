import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    
    # Database
    DB_HOST = os.getenv('DB_HOST', 'db')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'radius')
    DB_USER = os.getenv('DB_USER', 'radius')
    _db_password = os.getenv('DB_PASSWORD')
    if not _db_password:
        raise RuntimeError(
            'DB_PASSWORD is not set. Add it to .env (see .env.example).'
        )
    DB_PASSWORD = _db_password
    
    SQLALCHEMY_DATABASE_URI = (
        f'mysql+pymysql://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}'
        f'@{DB_HOST}:{DB_PORT}/{quote_plus(DB_NAME)}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # FreeRADIUS
    RADIUS_SECRET = os.getenv('RADIUS_SECRET', 'testing123')
    
    # Admin
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@safenet.local')
    
    # Guest Wi-Fi branding (public /portal page and printed vouchers)
    HOTSPOT_NAME = os.getenv('HOTSPOT_NAME', 'SafeNet WiFi')
    HOTSPOT_SSID = os.getenv('HOTSPOT_SSID', '')
    HOTSPOT_SUPPORT = os.getenv('HOTSPOT_SUPPORT', '')  # phone/WhatsApp shown to guests
    HOTSPOT_CURRENCY = os.getenv('HOTSPOT_CURRENCY', 'TZS')
    HOTSPOT_TERMS = os.getenv(
        'HOTSPOT_TERMS',
        'Use this network lawfully. No illegal downloads, spam or attacks on other users. '
        'Vouchers are valid from first login, cannot be refunded and must not be shared. '
        'We may log connection times and data usage for billing and security.'
    )

    # ClickPesa mobile-money collection (Settings -> Developers in ClickPesa)
    CLICKPESA_CLIENT_ID = os.getenv('CLICKPESA_CLIENT_ID', '')
    CLICKPESA_API_KEY = os.getenv('CLICKPESA_API_KEY', '')
    CLICKPESA_CHECKSUM_KEY = os.getenv('CLICKPESA_CHECKSUM_KEY', '')  # only if checksum is enabled
    CLICKPESA_BASE_URL = os.getenv('CLICKPESA_BASE_URL', 'https://api.clickpesa.com')

    # Platform-collected payments: default fee kept by the platform, minimum payout
    PLATFORM_FEE_PERCENT = float(os.getenv('PLATFORM_FEE_PERCENT', '3'))   # SafeNet Pay fee on tenants' sales
    SMS_PRICE = int(os.getenv('SMS_PRICE', '30'))      # TZS per SMS sent to a tenant's guest, charged to the tenant
    # Tenant subscriptions: days of service after a trial/paid period ends
    BILLING_GRACE_DAYS = int(os.getenv('BILLING_GRACE_DAYS', '3'))
    BILLING_REMINDERS = os.getenv('BILLING_REMINDERS', 'true').lower() == 'true'
    MIN_WITHDRAWAL = int(os.getenv('MIN_WITHDRAWAL', '5000'))
    # Fernet key for secrets stored in the database (derived from SECRET_KEY if empty)
    DATA_ENCRYPTION_KEY = os.getenv('DATA_ENCRYPTION_KEY', '')

    # WireGuard hub that tenants' routers connect to (safenet-wireguard service)
    WG_ENDPOINT = os.getenv('WG_ENDPOINT', 'radius.safezonetz.com')   # public host routers dial
    # Omada Controller run by SafeNet: tenants' Omada access points adopt to it
    OMADA_HOSTED_URL = os.getenv('OMADA_HOSTED_URL', '').rstrip('/')          # e.g. https://127.0.0.1:8043
    OMADA_HOSTED_USER = os.getenv('OMADA_HOSTED_USER', '')
    OMADA_HOSTED_PASSWORD = os.getenv('OMADA_HOSTED_PASSWORD', '')
    OMADA_HOSTED_HOST = os.getenv('OMADA_HOSTED_HOST', '') or WG_ENDPOINT    # what access points are told to use
    OMADA_DASHBOARD_URL = os.getenv('OMADA_DASHBOARD_URL', 'https://omada.safezonetz.com').rstrip('/')   # where people sign in
    # Open API app on SafeNet's controller: lets tenants add access points from SafeNet alone
    OMADA_OPENAPI_CLIENT_ID = os.getenv('OMADA_OPENAPI_CLIENT_ID', '')
    OMADA_OPENAPI_CLIENT_SECRET = os.getenv('OMADA_OPENAPI_CLIENT_SECRET', '')
    # WiFiDog access points call SafeNet over plain HTTP (many can't follow the HTTPS redirect of
    # the public site), so they use the app port directly; guests' browsers move to HTTPS.
    WIFIDOG_BASE = os.getenv('WIFIDOG_BASE', f'http://{WG_ENDPOINT}:5001').rstrip('/')
    WG_PORT = int(os.getenv('WG_PORT', '51820'))
    WG_SERVER_IP = os.getenv('WG_SERVER_IP', '10.200.0.1')           # hub's tunnel address = RADIUS server
    WG_SUBNET = os.getenv('WG_SUBNET', '10.200.0.0/16')

    # Mobile-money networks the platform ClickPesa account accepts, in display
    # order, with an optional minimum amount: e.g. "mpesa,mixx:1000,airtel,halopesa"
    PAYMENT_NETWORKS = os.getenv('PAYMENT_NETWORKS', 'mixx:1000,airtel,halopesa')   # ClickPesa
    # Snippe (second mobile-money provider; supports Vodacom M-Pesa). Keys from the Snippe dashboard.
    SNIPPE_API_KEY = os.getenv('SNIPPE_API_KEY', '')
    SNIPPE_WEBHOOK_KEY = os.getenv('SNIPPE_WEBHOOK_KEY', '')          # Settings -> Webhook Secret
    SNIPPE_BASE_URL = os.getenv('SNIPPE_BASE_URL', 'https://api.snippe.sh')
    SNIPPE_NETWORKS = os.getenv('SNIPPE_NETWORKS', 'mpesa,mixx,airtel,halopesa')
    SNIPPE_CUSTOMER_EMAIL = os.getenv('SNIPPE_CUSTOMER_EMAIL', 'wifi@safezonetz.com')   # Snippe requires one
    # Which provider SafeNet Pay uses until the platform admin picks one in Platform: Billing
    PAYMENT_PROVIDER = os.getenv('PAYMENT_PROVIDER', 'snippe')     # SafeNet Pay's provider until the platform admin picks one

    # Shared key captive-portal gateways send in X-SafeNet-Key (empty = API disabled)
    PORTAL_API_KEY = os.getenv('PORTAL_API_KEY', '')

    # Public address of this app, used in emailed links (verification, password reset)
    PUBLIC_URL = os.getenv('PUBLIC_URL', 'https://radius.safezonetz.com').rstrip('/')
    # Cookies only over HTTPS (the app is also reachable over plain HTTP on :5001 for access points),
    # not sent with cross-site posts, and not readable by scripts
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', '1' if PUBLIC_URL.startswith('https') else '0') == '1'
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SAMESITE = 'Lax'

    # Self-service signup
    SIGNUP_ENABLED = os.getenv('SIGNUP_ENABLED', 'true').lower() == 'true'
    TRIAL_DAYS = int(os.getenv('TRIAL_DAYS', '14'))

    # Outgoing email
    MAIL_SERVER = os.getenv('MAIL_SERVER', '')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '465'))
    # 465 = implicit TLS (SMTP_SSL); anything else uses STARTTLS
    MAIL_USE_SSL = (os.getenv('MAIL_USE_SSL') or ('true' if os.getenv('MAIL_PORT', '465') == '465' else 'false')).lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', '')

    # SMS (NextSMS): payment confirmations with voucher codes, billing notices
    NEXTSMS_USERNAME = os.getenv('NEXTSMS_USERNAME', '')
    NEXTSMS_PASSWORD = os.getenv('NEXTSMS_PASSWORD', '')
    NEXTSMS_SENDER_ID = os.getenv('NEXTSMS_SENDER_ID', '')
    NEXTSMS_URL = os.getenv('NEXTSMS_URL', 'https://messaging-service.co.tz/api/sms/v1/text/single')

    # Pagination
    ITEMS_PER_PAGE = 25
    
    # Supported vendors
    SUPPORTED_VENDORS = [
        ('standard', 'Standard RADIUS'),
        ('cisco', 'Cisco'),
        ('mikrotik', 'MikroTik'),
        ('tplink', 'TP-Link'),
        ('dlink', 'D-Link'),
        ('ubiquiti', 'UniFi / Ubiquiti'),
        ('aruba', 'Aruba'),
    ]
    
    # Common RADIUS attributes
    COMMON_ATTRIBUTES = [
        'Session-Timeout',
        'Idle-Timeout',
        'Acct-Interim-Interval',
        'Framed-IP-Address',
        'Framed-IP-Netmask',
        'Framed-Route',
        'Filter-Id',
        'Reply-Message',
    ]
    
    # Vendor-specific attributes
    VENDOR_ATTRIBUTES = {
        'cisco': [
            'Cisco-AVPair',
            'Cisco-Account-Info',
            'Cisco-Service-Info',
        ],
        'mikrotik': [
            'Mikrotik-Rate-Limit',
            'Mikrotik-Recv-Limit',
            'Mikrotik-Xmit-Limit',
            'Mikrotik-Group',
            'Mikrotik-Address-List',
        ],
        'ubiquiti': [
            'Ubiquiti-Data-Limit-Down',
            'Ubiquiti-Data-Limit-Up',
            'Ubiquiti-VLAN-ID',
        ],
        'aruba': [
            'Aruba-User-Role',
            'Aruba-Admin-Role',
        ],
    }


