from flask_wtf import FlaskForm as _FlaskForm
from flask_wtf.file import FileField
import snippe
from wtforms import StringField, PasswordField, TextAreaField, SelectField, BooleanField, IntegerField, DateTimeField
from wtforms.validators import DataRequired, Email, Length, Optional, IPAddress, ValidationError
from models import Admin, Plan, RadUser, Nas
from i18n import L, tr
import re


class _Translations:
    """WTForms' own messages ("This field is required." and the like) in the dashboard language."""
    def gettext(self, text):
        return tr(text)

    def ngettext(self, singular, plural, n):
        return tr(singular if n == 1 else plural)


class FlaskForm(_FlaskForm):
    """FlaskForm with WTForms' built-in messages translated."""
    class Meta:
        def get_translations(self, form):
            return _Translations()


_SPEED_RE = re.compile(r'^\s*(\d+(?:[.,]\d+)?)\s*(k|kb|kbit|kbps|kb/s|m|mb|mbit|mbps|mb/s|g|gb|gbit|gbps|gb/s)?\s*$', re.I)


def normalize_speed(text):
    """'5', '5M', '5 Mbps', '5Mb/s', '512k', '1.5 Mbps' -> '5M', '512k', '1500k'. '' -> ''. None if unreadable.
    One format (bits per second, k/M/G) that the gateway, MikroTik and Omada all understand."""
    text = (text or '').strip()
    if not text:
        return ''
    m = _SPEED_RE.match(text)
    if not m:
        return None
    value = float(m.group(1).replace(',', '.'))
    unit = (m.group(2) or 'm')[0].lower()
    kbps = value * {'k': 1, 'm': 1000, 'g': 1000000}[unit]
    if kbps < 8:
        return None
    if kbps % 1000000 == 0:
        return f'{int(kbps // 1000000)}G'
    if kbps % 1000 == 0:
        return f'{int(kbps // 1000)}M'
    return f'{int(round(kbps))}k'


class SpeedField(StringField):
    """Speed limit in bits per second, saved as e.g. 5M; empty means no limit."""
    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)
        self.raw_speed = self.data
        normal = normalize_speed(self.data)
        self.data = normal if normal is not None else self.data

    def pre_validate(self, form):
        if normalize_speed(getattr(self, 'raw_speed', self.data)) is None:
            raise ValidationError(L('Write the speed like 5M (5 Mb/s), 20M or 512k (512 kb/s).'))


class LoginForm(FlaskForm):
    """Admin login form"""
    username = StringField(L('Username'), validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField(L('Password'), validators=[DataRequired()])


class AdminForm(FlaskForm):
    """Admin user management form"""
    username = StringField(L('Username'), validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField(L('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(L('Password'), validators=[Optional(), Length(min=6)])
    is_active = BooleanField(L('Active'))
    
    def validate_username(self, field):
        if not re.match(r'^[a-zA-Z0-9_-]+$', field.data):
            raise ValidationError(L('Username can only contain letters, numbers, hyphens, and underscores.'))


class PlanForm(FlaskForm):
    """Plan/Group management form"""
    name = StringField(L('Plan Name'), validators=[DataRequired(), Length(min=2, max=64)])
    description = TextAreaField(L('Description'), validators=[Optional()])
    vendor = SelectField(L('Default Vendor'), validators=[DataRequired()])
    is_active = BooleanField(L('Active'), default=True)
    # Bandwidth limits
    upload_speed = SpeedField(L('Upload Speed'), validators=[Optional()],
                              description=L('e.g. 2M, 5M, 512k (Mb/s or kb/s). Leave empty for no limit.'))
    download_speed = SpeedField(L('Download Speed'), validators=[Optional()],
                                description=L('e.g. 5M, 20M (Mb/s). Leave empty for no limit.'))
    data_cap = IntegerField(L('Data Cap (GB)'), validators=[Optional()],
                           description=L('Data limit in GB (0 = unlimited)'))
    data_cap_period = SelectField(L('Data Cap Period'), choices=[
        ('daily', L('Daily')),
        ('weekly', L('Weekly')),
        ('monthly', L('Monthly'))
    ], default='monthly', validators=[Optional()],
    description=L('Reset period for data cap'))
    
    def validate_name(self, field):
        if not re.match(r'^[a-zA-Z0-9_-]+$', field.data):
            raise ValidationError(L('Plan name can only contain letters, numbers, hyphens, and underscores.'))


class PlanAttributeForm(FlaskForm):
    """Plan attribute form"""
    attribute = StringField(L('Attribute'), validators=[DataRequired(), Length(max=64)])
    op = SelectField(L('Operator'), choices=[
        (':=', L(':= (Assign)')),
        ('==', L('== (Equal)')),
        ('+=', L('+= (Add)')),
        ('!=', L('!= (Not Equal)')),
        ('>', L('> (Greater Than)')),
        ('<', L('< (Less Than)')),
        ('>=', L('>= (Greater or Equal)')),
        ('<=', L('<= (Less or Equal)')),
    ], validators=[DataRequired()])
    value = StringField(L('Value'), validators=[DataRequired(), Length(max=253)])
    vendor = SelectField(L('Vendor'), validators=[Optional()])
    priority = IntegerField(L('Priority'), default=0, validators=[Optional()])


class UserForm(FlaskForm):
    """RADIUS user management form"""
    username = StringField(L('Username'), validators=[DataRequired(), Length(min=3, max=64)])
    password = StringField(L('Password'), validators=[DataRequired(), Length(min=4)])
    plan_id = SelectField(L('Plan'), coerce=int, validators=[Optional()])
    is_active = BooleanField(L('Active'), default=True)
    expires_at = DateTimeField(L('Expires At'), format='%Y-%m-%d %H:%M:%S', validators=[Optional()])
    notes = TextAreaField(L('Notes'), validators=[Optional()])
    # Bandwidth limits (override plan limits if set)
    upload_speed = SpeedField(L('Upload Speed'), validators=[Optional()],
                              description=L('Override the plan, e.g. 5M or 512k (leave empty to use the plan)'))
    download_speed = SpeedField(L('Download Speed'), validators=[Optional()],
                                description=L('Override the plan, e.g. 20M (leave empty to use the plan)'))
    data_cap = IntegerField(L('Data Cap (GB)'), validators=[Optional()],
                           description=L('Override plan: Data limit in GB (0 = unlimited, leave empty to use plan default)'))
    data_cap_period = SelectField(L('Data Cap Period'), choices=[
        ('daily', L('Daily')),
        ('weekly', L('Weekly')),
        ('monthly', L('Monthly'))
    ], default='monthly', validators=[Optional()],
    description=L('Reset period for data cap (overrides plan default)'))
    
    def validate_username(self, field):
        if not re.match(r'^[a-zA-Z0-9_.-]+$', field.data):
            raise ValidationError(L('Username can only contain letters, numbers, dots, hyphens, and underscores.'))


class NasForm(FlaskForm):
    """NAS device management form"""
    nasname = StringField(L('IP Address'), validators=[DataRequired(), IPAddress()])
    shortname = StringField(L('Short Name'), validators=[DataRequired(), Length(min=2, max=32)])
    type = SelectField(L('Type'), choices=[
        ('other', L('Other')),
        ('cisco', 'Cisco'),
        ('computone', 'Computone'),
        ('livingston', 'Livingston'),
        ('juniper', 'Juniper'),
        ('max40xx', 'Max40xx'),
        ('multitech', 'Multitech'),
        ('netserver', 'Netserver'),
        ('pathras', 'Pathras'),
        ('patton', 'Patton'),
        ('portslave', 'Portslave'),
        ('tc', 'TC'),
        ('usrhiper', 'USR Hiper'),
    ], validators=[DataRequired()])
    secret = StringField(L('RADIUS Secret'), validators=[DataRequired(), Length(min=6, max=60)])
    vendor = SelectField(L('Vendor'), validators=[DataRequired()])
    ports = IntegerField(L('Ports'), validators=[Optional()])
    server = StringField(L('Server'), validators=[Optional(), Length(max=64)])
    community = StringField(L('SNMP Community'), validators=[Optional(), Length(max=50)])
    description = StringField(L('Description'), validators=[Optional(), Length(max=200)])
    is_active = BooleanField(L('Active'), default=True)
    
    def validate_shortname(self, field):
        if not re.match(r'^[a-zA-Z0-9_-]+$', field.data):
            raise ValidationError(L('Short name can only contain letters, numbers, hyphens, and underscores.'))


class SearchForm(FlaskForm):
    """Generic search form"""
    query = StringField(L('Search'), validators=[Optional(), Length(max=100)])




class VoucherGenerateForm(FlaskForm):
    """Generate a batch of prepaid vouchers"""
    plan_id = SelectField(L('Plan'), coerce=int, validators=[Optional()])
    count = IntegerField(L('How many'), default=10, validators=[DataRequired()])
    validity_value = IntegerField(L('Valid for'), default=1, validators=[DataRequired()])
    validity_unit = SelectField(L('Unit'), choices=[
        ('hours', L('Hours')),
        ('days', L('Days')),
    ], default='days', validators=[DataRequired()])
    price = StringField(L('Price'), validators=[Optional(), Length(max=12)],
                        description=L('Printed on the voucher, e.g. 1000'))
    batch = StringField(L('Batch name'), validators=[Optional(), Length(max=64)],
                        description=L('Leave empty to name it by date/time'))
    max_devices = IntegerField(L('Devices per voucher'), default=1, validators=[DataRequired()],
                               description=L('How many devices can use one code at the same time'))
    is_free = BooleanField(L('Free trial (marketing)'),
                           description=L('Given away to let people try the Wi-Fi: no price, not counted as sales, '
                                         'and each phone can use only one free trial.'))

    def validate_max_devices(self, field):
        if not 1 <= (field.data or 0) <= 10:
            raise ValidationError(L('Choose between 1 and 10 devices.'))

    def validate_count(self, field):
        if not 1 <= (field.data or 0) <= 500:
            raise ValidationError(L('Generate between 1 and 500 vouchers at a time.'))

    def validate_validity_value(self, field):
        if not 1 <= (field.data or 0) <= 365:
            raise ValidationError(L('Enter a value between 1 and 365.'))

    def validate_price(self, field):
        if field.data and not re.match(r'^\d+(\.\d{1,2})?$', field.data.strip()):
            raise ValidationError(L('Price must be a number, e.g. 1000 or 1500.50'))


class PackageForm(FlaskForm):
    """Internet package sold on the captive portal"""
    name = StringField(L('Package name'), validators=[DataRequired(), Length(max=64)],
                       description=L('Shown to guests, e.g. "1 Hour - 500"'))
    description = StringField(L('Short description'), validators=[Optional(), Length(max=200)])
    plan_id = SelectField(L('Speed plan'), coerce=int, validators=[Optional()])
    price = StringField(L('Price (TZS)'), validators=[DataRequired(), Length(max=12)])
    validity_value = IntegerField(L('Access duration'), default=1, validators=[DataRequired()])
    validity_unit = SelectField(L('Unit'), choices=[
        ('minutes', L('Minutes')),
        ('hours', L('Hours')),
        ('days', L('Days')),
    ], default='hours', validators=[DataRequired()])
    sort_order = IntegerField(L('Display order'), default=0, validators=[Optional()],
                              description=L('Lower numbers are shown first'))
    max_devices = IntegerField(L('Devices allowed'), default=1, validators=[DataRequired()],
                               description=L('How many devices can use one purchase at the same time'))
    is_active = BooleanField(L('Active'), default=True)
    show_on_portal = BooleanField(L('Show on captive portal'), default=True)

    def validate_price(self, field):
        value = (field.data or '').strip()
        if not re.match(r'^\d+(\.\d{1,2})?$', value) or float(value) < 100:
            raise ValidationError(L('Enter a price of at least 100, e.g. 500 or 1000.'))

    def validate_validity_value(self, field):
        if not 1 <= (field.data or 0) <= 100000:
            raise ValidationError(L('Enter a positive duration.'))

    def validate_max_devices(self, field):
        if not 1 <= (field.data or 0) <= 10:
            raise ValidationError(L('Choose between 1 and 10 devices.'))


class SignupForm(FlaskForm):
    """Self-service signup: creates a tenant and its owner"""
    business_name = StringField(L('Business name'), validators=[DataRequired(), Length(min=2, max=100)])
    username = StringField(L('Username'), validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField(L('Email'), validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField(L('Phone'), validators=[Optional(), Length(max=20)])
    password = PasswordField(L('Password'), validators=[DataRequired(), Length(min=8, max=128)])
    confirm = PasswordField(L('Confirm password'), validators=[DataRequired()])
    accept = BooleanField(L('I accept the terms of service'), validators=[DataRequired()])

    def validate_username(self, field):
        if not re.match(r'^[a-zA-Z0-9_.-]+$', field.data):
            raise ValidationError(L('Use letters, numbers, dots, hyphens and underscores only.'))

    def validate_confirm(self, field):
        if field.data != self.password.data:
            raise ValidationError(L('Passwords do not match.'))


class EmailForm(FlaskForm):
    """Resend verification / forgot password"""
    email = StringField(L('Email'), validators=[DataRequired(), Email()])


class ResetPasswordForm(FlaskForm):
    password = PasswordField(L('New password'), validators=[DataRequired(), Length(min=8, max=128)])
    confirm = PasswordField(L('Confirm password'), validators=[DataRequired()])

    def validate_confirm(self, field):
        if field.data != self.password.data:
            raise ValidationError(L('Passwords do not match.'))


class TenantSettingsForm(FlaskForm):
    name = StringField(L('Business name'), validators=[DataRequired(), Length(max=100)])
    phone = StringField(L('Business phone'), validators=[Optional(), Length(max=20)])
    hotspot_name = StringField(L('Wi-Fi name shown to guests'), validators=[Optional(), Length(max=64)],
                               description=L('On the splash page and printed vouchers. Defaults to the business name.'))
    support_phone = StringField(L('Support phone / WhatsApp'), validators=[Optional(), Length(max=32)])
    currency = StringField(L('Currency'), validators=[DataRequired(), Length(min=3, max=3)])
    terms = TextAreaField(L('Terms of use for guests'), validators=[Optional(), Length(max=4000)])
    block_tethering = BooleanField(L('Block hotspot sharing'),
                                   description=L("Guests can't share their internet with other devices through their phone or laptop hotspot."))


class TeamMemberForm(FlaskForm):
    username = StringField(L('Username'), validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField(L('Email'), validators=[DataRequired(), Email(), Length(max=120)])
    role = SelectField(L('Role'), choices=[('viewer', L('Partner / shareholder: view only (finance and usage)')),
                                        ('staff', L('Staff: users, vouchers, live')),
                                        ('admin', L('Admin: everything except team owners'))], default='staff')
    site_id = SelectField(L('Can see'), coerce=int, default=0,
                          description=L('For partners: the whole business, or only one site.'))
    password = PasswordField(L('Temporary password'), validators=[DataRequired(), Length(min=8, max=128)])

    def validate_username(self, field):
        if not re.match(r'^[a-zA-Z0-9_.-]+$', field.data):
            raise ValidationError(L('Use letters, numbers, dots, hyphens and underscores only.'))


class GatewayForm(FlaskForm):
    name = StringField(L('Gateway name'), validators=[DataRequired(), Length(max=64)],
                       description=L('e.g. "Main branch - dev server"'))


class PaymentSettingsForm(FlaskForm):
    payment_mode = SelectField(L('Who receives package payments?'), choices=[
        ('platform', L('SafeNet Pay collects for me, I withdraw my balance')),
        ('own', L('Straight into my own ClickPesa or Snippe account')),
    ])
    own_provider = SelectField(L('My payment account'), choices=[('snippe', 'Snippe'), ('clickpesa', 'ClickPesa')])
    snippe_api_key = PasswordField(L('Snippe API key'), validators=[Optional(), Length(max=200)],
                                   description=L('Starts with snp_. Leave empty to keep the saved key.'))
    snippe_webhook_key = PasswordField(L('Snippe webhook signing key'), validators=[Optional(), Length(max=200)],
                                       description=L('Snippe dashboard: Settings -> Webhook Secret. Leave empty to keep the saved key.'))
    client_id = StringField(L('ClickPesa Client ID'), validators=[Optional(), Length(max=64)])
    api_key = PasswordField(L('ClickPesa API key'), validators=[Optional(), Length(max=200)],
                            description=L('Leave empty to keep the saved key.'))
    checksum_key = PasswordField(L('Checksum key (only if enabled in ClickPesa)'), validators=[Optional(), Length(max=200)],
                                 description=L('Leave empty to keep the saved key.'))
    clear_checksum = BooleanField(L('Remove the saved checksum key'))


LIPA_NETWORKS = ('Vodacom M-Pesa', 'Mixx by Yas', 'Airtel Money', 'HaloPesa', 'CRDB Bank', 'NMB Bank', 'Other')


class WithdrawalForm(FlaskForm):
    amount = IntegerField(L('Amount'), validators=[DataRequired()])
    method = SelectField(L('Send it to'), choices=[('mobile', L('Mobile money number')), ('lipa', L('Lipa Namba (merchant till)')),
                                                ('bank', L('Bank account'))], default='mobile')
    phone = StringField(L('Mobile number'), validators=[DataRequired(), Length(max=20)],
                        description=L('Mobile money is sent here. For Lipa Namba or bank, we SMS this number when it is paid.'))
    lipa_namba = StringField(L('Lipa Namba'), validators=[Optional(), Length(max=20)])
    lipa_network = SelectField(L('Lipa Namba network'), choices=[('', L('Choose…'))] + [(n, n) for n in LIPA_NETWORKS], default='')
    bank_name = SelectField(L('Bank'), choices=[('', L('Choose…'))] + [(b, b) for b in snippe.BANKS], default='')
    bank_account = StringField(L('Account number'), validators=[Optional(), Length(max=40)])
    account_name = StringField(L('Account name'), validators=[Optional(), Length(max=100)],
                               description=L('Name registered on the number, till or bank account'))



class PortalSettingsForm(FlaskForm):
    """How the captive portal looks to guests"""
    color = StringField(L('Brand colour'), validators=[DataRequired()])
    style = SelectField(L('Header style'), choices=[('gradient', L('Gradient')), ('solid', L('Solid colour')), ('light', L('Light (white)'))])
    title = StringField(L('Welcome title'), validators=[Optional(), Length(max=80)],
                        description=L('Leave empty for "Welcome to <your Wi-Fi name>".'))
    message = TextAreaField(L('Welcome message'), validators=[Optional(), Length(max=300)],
                            description=L('One or two short sentences under the title.'))
    language = SelectField(L('Default language'), choices=[('en', 'English'), ('sw', 'Kiswahili')])
    show_voucher = BooleanField(L('Voucher login'))
    show_packages = BooleanField(L('Buy packages with mobile money'))
    logo = FileField(L('Logo (PNG, JPG or WebP, up to 300 KB)'))
    remove_logo = BooleanField(L('Remove the current logo'))

    def validate_color(self, field):
        if not re.fullmatch(r'#[0-9a-fA-F]{6}', field.data or ''):
            raise ValidationError(L('Use a colour like #051D60.'))

    def validate_show_packages(self, field):
        if not field.data and not self.show_voucher.data:
            raise ValidationError(L('Keep at least one way to get online.'))
