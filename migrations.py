"""Idempotent schema upgrades, run by `flask init-db` on every start.

db.create_all() creates missing tables but never alters existing ones, and the
FreeRADIUS tables come from database/schema.sql. Each step here checks the live
schema first, so it is safe on a fresh database and on one upgraded many times.
"""
from datetime import datetime, timedelta

from sqlalchemy import inspect, text

from config import Config
from models import db, Tenant, Admin

DEFAULT_TENANT_SLUG = 'safenet'
TENANT_TABLES = ('admins', 'plans', 'nas', 'radusers', 'vouchers', 'packages', 'payments')


def _q(name):
    """Quote an identifier (index `name` on plans is a keyword in MariaDB)."""
    return f'`{name}`' if db.engine.dialect.name == 'mysql' else f'"{name}"'


def _columns(table):
    return {c['name'] for c in inspect(db.engine).get_columns(table)}


def _indexes(table):
    insp = inspect(db.engine)
    names = {i['name'] for i in insp.get_indexes(table)}
    names |= {u['name'] for u in insp.get_unique_constraints(table) if u.get('name')}
    return names


def _add_column(table, column, ddl):
    if column not in _columns(table):
        db.session.execute(text(f'ALTER TABLE {_q(table)} ADD COLUMN {_q(column)} {ddl}'))
        db.session.commit()
        print(f'migrate: added {table}.{column}')
        return True
    return False


def _add_index(table, name, columns, unique=False):
    if name not in _indexes(table):
        cols = ', '.join(_q(c.strip()) for c in columns.split(','))
        db.session.execute(text(f'CREATE {"UNIQUE " if unique else ""}INDEX {_q(name)} ON {_q(table)} ({cols})'))
        db.session.commit()
        print(f'migrate: created index {name}')


def _drop_unique_index(table, name):
    insp = inspect(db.engine)
    unique = {i['name'] for i in insp.get_indexes(table) if i.get('unique')}
    unique |= {u['name'] for u in insp.get_unique_constraints(table) if u.get('name')}
    if name in unique:
        sql = f'DROP INDEX {_q(name)} ON {_q(table)}' if db.engine.dialect.name == 'mysql' else f'DROP INDEX {_q(name)}'
        db.session.execute(text(sql))
        db.session.commit()
        print(f'migrate: dropped unique index {name}')


def default_tenant():
    tenant = Tenant.query.filter_by(slug=DEFAULT_TENANT_SLUG).first()
    if not tenant:
        tenant = Tenant(name='SafeNet', slug=DEFAULT_TENANT_SLUG, status='active')
        db.session.add(tenant)
        db.session.commit()
        print('migrate: created default tenant')
    return tenant


def _as_datetime(value):
    """SQLite returns DATETIME columns from raw SQL as strings."""
    return datetime.fromisoformat(str(value)) if not isinstance(value, datetime) else value


def _default_tenant_id():
    """Default tenant's id via plain SQL, so it works before the ORM's columns exist."""
    row = db.session.execute(text('SELECT id FROM tenants WHERE slug = :s'), {'s': DEFAULT_TENANT_SLUG}).first()
    if row:
        return row[0]
    db.session.execute(text("INSERT INTO tenants (name, slug, status, currency, payment_mode, created_at) "
                            "VALUES ('SafeNet', :s, 'active', 'TZS', 'platform', :now)"),
                       {'s': DEFAULT_TENANT_SLUG, 'now': datetime.utcnow()})
    db.session.commit()
    print('migrate: created default tenant')
    return _default_tenant_id()


def run():
    # Columns of tables that are read during the upgrade come first: never use
    # ORM queries on a table before all of its model's columns exist.
    # Payments in both modes (phase 3)
    _add_column('tenants', 'payment_mode', "VARCHAR(16) NOT NULL DEFAULT 'platform'")
    _add_column('tenants', 'clickpesa_client_id', 'VARCHAR(64) NULL')
    _add_column('tenants', 'clickpesa_api_key_enc', 'TEXT NULL')
    _add_column('tenants', 'clickpesa_checksum_key_enc', 'TEXT NULL')
    _add_column('tenants', 'fee_percent', 'NUMERIC(5, 2) NULL')
    _add_column('tenants', 'own_provider', "VARCHAR(16) NOT NULL DEFAULT 'clickpesa'")
    _add_column('tenants', 'sms_to_guests', 'BOOLEAN NOT NULL DEFAULT 1')
    _add_column('tenants', 'sms_changed_at', 'DATETIME NULL')
    _add_column('tenants', 'notify_phone', 'VARCHAR(16) NULL')
    _add_column('tenants', 'notify_sale_sms', 'BOOLEAN NOT NULL DEFAULT 0')
    _add_column('tenants', 'notify_daily_sms', 'BOOLEAN NOT NULL DEFAULT 0')
    _add_column('tenants', 'notify_daily_email', 'BOOLEAN NOT NULL DEFAULT 0')
    _add_column('tenants', 'summary_sent_on', 'DATE NULL')
    _add_column('tenants', 'omada_login', 'VARCHAR(64) NULL')
    _add_column('tenants', 'omada_user_id', 'VARCHAR(64) NULL')
    _add_column('tenants', 'omada_password_enc', 'TEXT NULL')
    _add_column('subscription_payments', 'sms_amount', 'NUMERIC(10, 2) NOT NULL DEFAULT 0')
    _add_column('admins', 'site_id', 'INTEGER NULL')
    _add_column('admins', 'language', "VARCHAR(2) NOT NULL DEFAULT 'en'")
    _add_column('tenants', 'snippe_api_key_enc', 'TEXT NULL')
    _add_column('tenants', 'snippe_webhook_key_enc', 'TEXT NULL')
    _add_column('tenants', 'billing_plan_id', 'INTEGER NULL')
    _add_column('tenants', 'paid_until', 'DATETIME NULL')
    if _add_column('tenants', 'service_until', 'DATETIME NULL'):
        # Trials that existed before billing: service ends after the trial + grace
        grace = timedelta(days=Config.BILLING_GRACE_DAYS)
        for tid, trial_end in db.session.execute(text(
                "SELECT id, trial_ends_at FROM tenants WHERE status = 'trial' AND trial_ends_at IS NOT NULL")).all():
            db.session.execute(text('UPDATE tenants SET service_until = :u WHERE id = :i'),
                               {'u': _as_datetime(trial_end) + grace, 'i': tid})
        db.session.commit()
    _add_column('tenants', 'billing_notice', 'VARCHAR(32) NULL')
    # Captive portal customisation
    _add_column('tenants', 'portal_color', 'VARCHAR(7) NULL')
    _add_column('tenants', 'portal_style', 'VARCHAR(16) NULL')
    _add_column('tenants', 'portal_title', 'VARCHAR(80) NULL')
    _add_column('tenants', 'portal_message', 'VARCHAR(300) NULL')
    _add_column('tenants', 'portal_language', 'VARCHAR(2) NULL')
    _add_column('tenants', 'portal_show_voucher', 'BOOLEAN NOT NULL DEFAULT 1')
    _add_column('tenants', 'portal_show_packages', 'BOOLEAN NOT NULL DEFAULT 1')
    _add_column('tenants', 'portal_logo', 'MEDIUMBLOB NULL' if db.engine.dialect.name == 'mysql' else 'BLOB NULL')
    _add_column('tenants', 'portal_logo_type', 'VARCHAR(32) NULL')
    _add_column('tenants', 'portal_logo_at', 'DATETIME NULL')
    _add_column('tenants', 'block_tethering', 'BOOLEAN NOT NULL DEFAULT 1')
    _add_column('payments', 'provider_account', "VARCHAR(16) NOT NULL DEFAULT 'platform'")
    _add_column('payments', 'fee_amount', 'NUMERIC(10, 2) NULL DEFAULT 0')
    _add_column('payments', 'net_amount', 'NUMERIC(10, 2) NULL')
    _add_column('payments', 'gift_phone', 'VARCHAR(16)')
    # Withdrawals to a Lipa Namba or bank, and payouts sent through ClickPesa
    _add_column('withdrawals', 'method', "VARCHAR(8) NOT NULL DEFAULT 'mobile'")
    for col, kind in (('lipa_namba', 'VARCHAR(20)'), ('lipa_network', 'VARCHAR(40)'), ('bank_name', 'VARCHAR(80)'),
                      ('bank_account', 'VARCHAR(40)'), ('payout_ref', 'VARCHAR(20)'), ('payout_status', 'VARCHAR(16)'),
                      ('payout_provider', 'VARCHAR(16)'), ('payout_id', 'VARCHAR(64)'),
                      ('payout_fee', 'NUMERIC(10, 2) NULL'), ('payout_receiver', 'VARCHAR(100)'), ('payout_error', 'VARCHAR(255)')):
        _add_column('withdrawals', col, kind)

    tid = _default_tenant_id()

    # Multi-tenancy: every owned row belongs to a tenant; existing data -> default tenant
    for table in TENANT_TABLES:
        _add_column(table, 'tenant_id', 'INTEGER NULL')
        db.session.execute(text(f'UPDATE {table} SET tenant_id = :t WHERE tenant_id IS NULL'), {'t': tid})
        db.session.commit()
        _add_index(table, f'ix_{table}_tenant_id', 'tenant_id')

    # Admin roles; admins that existed before tenants are the platform operators
    new_roles = _add_column('admins', 'role', "VARCHAR(16) NOT NULL DEFAULT 'owner'")
    _add_column('admins', 'is_superadmin', 'BOOLEAN NOT NULL DEFAULT 0')
    if _add_column('admins', 'email_verified_at', 'DATETIME NULL') or new_roles:
        db.session.execute(text('UPDATE admins SET is_superadmin = 1, email_verified_at = :now '
                                'WHERE email_verified_at IS NULL'), {'now': datetime.utcnow()})
        db.session.commit()

    # Plans: names unique per tenant; RADIUS group name fixed and globally unique
    _add_column('plans', 'group_name', 'VARCHAR(64) NULL')
    db.session.execute(text('UPDATE plans SET group_name = name WHERE group_name IS NULL'))
    db.session.commit()
    _drop_unique_index('plans', 'name')           # schema.sql: UNIQUE KEY name (name)
    _drop_unique_index('plans', 'ix_plans_name')  # older create_all: unique index on name
    _add_index('plans', 'ix_plans_name', 'name')
    _add_index('plans', 'uq_plans_tenant_name', 'tenant_id, name', unique=True)
    _add_index('plans', 'uq_plans_group_name', 'group_name', unique=True)

    db.session.execute(text('UPDATE payments SET fee_amount = 0, net_amount = amount WHERE net_amount IS NULL'))
    db.session.commit()

    # One code, limited devices (anti-sharing)
    for table in ('vouchers', 'packages', 'payments'):
        _add_column(table, 'max_devices', 'INTEGER NOT NULL DEFAULT 1')

    # Free-trial (marketing) vouchers: one per phone
    _add_column('vouchers', 'is_free', 'BOOLEAN NOT NULL DEFAULT 0')
    _add_column('vouchers', 'first_mac', 'VARCHAR(17)')

    # Plan limits for customers and staff, and a yearly price
    _add_column('billing_plans', 'price_yearly', 'NUMERIC(10, 2)')
    _add_column('billing_plans', 'max_customers', 'INTEGER')
    _add_column('billing_plans', 'max_staff', 'INTEGER')
    _add_column('billing_plans', 'max_sites', 'INTEGER')
    # "Sites" used to be counted as gateways: move those limits to real sites (once)
    db.session.execute(text('UPDATE billing_plans SET max_sites = max_gateways, max_gateways = NULL '
                            'WHERE max_sites IS NULL AND max_gateways IS NOT NULL'))
    db.session.commit()
    _seed_billing_plans()

    # Sites: every tenant has at least one; existing devices and sales go to it
    for table in ('gateways', 'routers', 'nas', 'packages', 'payments', 'vouchers'):
        _add_column(table, 'site_id', 'INTEGER')
    # TP-Link Omada external portal, per site
    _add_column('sites', 'portal_token', 'VARCHAR(24)')
    _add_column('sites', 'omada_url', 'VARCHAR(255)')
    _add_column('sites', 'omada_user', 'VARCHAR(64)')
    _add_column('sites', 'omada_password_enc', 'TEXT')
    _add_column('sites', 'omada_verify_tls', 'BOOLEAN NOT NULL DEFAULT 0')
    _add_column('sites', 'omada_hosted', 'BOOLEAN NOT NULL DEFAULT 0')
    _add_column('sites', 'omada_site_id', 'VARCHAR(64)')
    _add_column('sites', 'omada_ssid', 'VARCHAR(32)')
    _add_column('sites', 'omada_device_password_enc', 'TEXT')
    _add_column('sites', 'wifidog_enabled', 'BOOLEAN NOT NULL DEFAULT 0')
    _add_column('sites', 'wifidog_seen_at', 'DATETIME')
    _add_column('sites', 'wifidog_gw_id', 'VARCHAR(64)')
    _add_column('sites', 'omada_checked_at', 'DATETIME')
    _add_column('sites', 'omada_synced_at', 'DATETIME')
    _add_column('sites', 'wifi_ssid', 'VARCHAR(32)')
    _add_column('sites', 'wifi_password', 'VARCHAR(63)')
    _add_column('sites', 'omada_error', 'VARCHAR(255)')
    _add_index('sites', 'uq_sites_portal_token', 'portal_token', unique=True)
    _ensure_sites()
    _scrub_provider_messages()


STARTER_PLANS = (
    # name, monthly, yearly, customers, routers, sites (gateways), staff
    ('Starter', 10000, 110000, 200, 1, 1, 2),
    ('Business', 20000, 220000, 400, 10, 10, 10),
    ('Economic', 30000, 339000, 1000, 20, 16, 20),
)


def _seed_billing_plans():
    """First-time plans, only while there are none (edit them in Platform: Billing)."""
    from models import BillingPlan
    if db.session.query(BillingPlan.id).first():
        return
    for order, (name, month, year, customers, routers, sites, staff) in enumerate(STARTER_PLANS):
        db.session.add(BillingPlan(name=name, price=month, price_yearly=year, currency='TZS', max_customers=customers,
                                   max_routers=routers, max_sites=sites, max_staff=staff, sort_order=order))
    db.session.commit()
    print('migrate: added starter billing plans')


def _ensure_sites():
    now = datetime.utcnow()
    for (tid,) in db.session.execute(text('SELECT id FROM tenants WHERE id NOT IN (SELECT tenant_id FROM sites)')).all():
        db.session.execute(text('INSERT INTO sites (tenant_id, name, created_at) VALUES (:t, :n, :c)'),
                           {'t': tid, 'n': 'Main site', 'c': now})
        print(f'migrate: created main site for tenant {tid}')
    # Anything without a site (packages excepted: no site = sold everywhere) goes to the tenant's first site
    first = '(SELECT MIN(s.id) FROM sites s WHERE s.tenant_id = {t}.tenant_id)'
    for table in ('gateways', 'routers', 'nas', 'payments', 'vouchers'):
        db.session.execute(text(f'UPDATE {table} SET site_id = {first.format(t=table)} '
                                f'WHERE site_id IS NULL AND tenant_id IS NOT NULL'))
    db.session.commit()


def _scrub_provider_messages():
    """Provider errors saved before they were cleaned may hold IDs or keys (e.g. a ClickPesa client id)."""
    import safetext
    targets = [(t, c) for t, c in (('withdrawals', 'payout_error'), ('payments', 'message'), ('subscription_payments', 'message'))
               if c in _columns(t)]        # look up columns first: inspecting mid-update can reset the connection
    for table, column in targets:
        rows = db.session.execute(text(
            f"SELECT id, {_q(column)} FROM {_q(table)} WHERE {_q(column)} LIKE '%Application%' OR {_q(column)} LIKE '%snp_%' "
            f"OR {_q(column)} LIKE '%Bearer%' OR {_q(column)} LIKE '%eyJ%'")).all()
        for row_id, value in rows:
            cleaned = safetext.clean(value)[:255]
            if cleaned != value:
                db.session.execute(text(f'UPDATE {_q(table)} SET {_q(column)} = :v WHERE id = :i'), {'v': cleaned, 'i': row_id})
                print(f'migrate: cleaned {table}.{column} #{row_id}')
        db.session.commit()
