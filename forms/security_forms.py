"""
Forms for Two-Factor Authentication and Security Settings
"""
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, IntegerField, SelectField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError
from wtforms.widgets import TextArea

class TwoFactorSetupForm(FlaskForm):
    """Form for setting up 2FA"""
    verification_code = StringField(
        'Verification Code', 
        validators=[
            DataRequired(),
            Length(min=6, max=6, message="Verification code must be 6 digits")
        ],
        render_kw={
            'placeholder': 'Enter 6-digit code from authenticator app',
            'autocomplete': 'off',
            'inputmode': 'numeric',
            'pattern': '[0-9]*'
        }
    )

class TwoFactorVerifyForm(FlaskForm):
    """Form for verifying 2FA during login"""
    token = StringField(
        'Authentication Code',
        validators=[
            DataRequired(),
            Length(min=6, max=6, message="Code must be 6 digits")
        ],
        render_kw={
            'placeholder': 'Enter 6-digit code',
            'autocomplete': 'off',
            'inputmode': 'numeric',
            'pattern': '[0-9]*'
        }
    )
    use_backup_code = BooleanField('Use backup code instead')

class BackupCodeForm(FlaskForm):
    """Form for using backup codes"""
    backup_code = StringField(
        'Backup Code',
        validators=[
            DataRequired(),
            Length(min=8, max=8, message="Backup code must be 8 digits")
        ],
        render_kw={
            'placeholder': 'Enter 8-digit backup code',
            'autocomplete': 'off'
        }
    )

class SecuritySettingsForm(FlaskForm):
    """Form for company security settings"""
    
    # 2FA Settings
    require_2fa = BooleanField('Require 2FA for all users')
    require_2fa_for_admins = BooleanField('Require 2FA for administrators', default=True)
    
    # Password Policy
    min_password_length = IntegerField(
        'Minimum Password Length',
        validators=[NumberRange(min=6, max=50)],
        default=8
    )
    require_uppercase = BooleanField('Require uppercase letters', default=True)
    require_lowercase = BooleanField('Require lowercase letters', default=True)
    require_numbers = BooleanField('Require numbers', default=True)
    require_special_chars = BooleanField('Require special characters', default=True)
    password_expiry_days = IntegerField(
        'Password Expiry (days)',
        validators=[NumberRange(min=0, max=365)],
        default=90,
        render_kw={'placeholder': '0 = never expires'}
    )
    
    # Login Security
    max_login_attempts = IntegerField(
        'Maximum Login Attempts',
        validators=[NumberRange(min=3, max=20)],
        default=5
    )
    lockout_duration_minutes = IntegerField(
        'Lockout Duration (minutes)',
        validators=[NumberRange(min=5, max=1440)],
        default=30
    )
    session_timeout_minutes = IntegerField(
        'Session Timeout (minutes)',
        validators=[NumberRange(min=15, max=480)],
        default=60
    )
    
    # IP Security
    allowed_ip_ranges = TextAreaField(
        'Allowed IP Ranges',
        render_kw={
            'placeholder': 'Enter IP ranges, one per line (e.g., 192.168.1.0/24)',
            'rows': 4
        }
    )
    block_suspicious_ips = BooleanField('Block suspicious IP addresses', default=True)

class PasswordChangeForm(FlaskForm):
    """Enhanced password change form with security validation"""
    current_password = PasswordField(
        'Current Password',
        validators=[DataRequired()],
        render_kw={'placeholder': 'Enter your current password'}
    )
    new_password = PasswordField(
        'New Password',
        validators=[DataRequired(), Length(min=8)],
        render_kw={'placeholder': 'Enter new password'}
    )
    confirm_password = PasswordField(
        'Confirm New Password',
        validators=[DataRequired()],
        render_kw={'placeholder': 'Confirm new password'}
    )
    
    def validate_confirm_password(self, field):
        if field.data != self.new_password.data:
            raise ValidationError('Passwords do not match')

class APIKeyForm(FlaskForm):
    """Form for API key management"""
    name = StringField(
        'API Key Name',
        validators=[DataRequired(), Length(min=3, max=100)],
        render_kw={'placeholder': 'e.g., Mobile App, Integration Service'}
    )
    description = TextAreaField(
        'Description',
        validators=[Optional(), Length(max=500)],
        render_kw={
            'placeholder': 'Description of what this API key will be used for',
            'rows': 3
        }
    )
    permissions = SelectField(
        'Permissions',
        choices=[
            ('read', 'Read Only'),
            ('write', 'Read & Write'),
            ('admin', 'Full Access')
        ],
        default='read'
    )
    expires_in_days = IntegerField(
        'Expires in (days)',
        validators=[NumberRange(min=1, max=365)],
        default=90,
        render_kw={'placeholder': 'Number of days until expiration'}
    )

class SingleSignOnForm(FlaskForm):
    """Form for SSO configuration"""
    provider = SelectField(
        'SSO Provider',
        choices=[
            ('saml', 'SAML 2.0'),
            ('oauth2', 'OAuth 2.0'),
            ('openid', 'OpenID Connect'),
            ('ldap', 'LDAP/Active Directory')
        ]
    )
    provider_name = StringField(
        'Provider Name',
        validators=[DataRequired(), Length(min=3, max=100)],
        render_kw={'placeholder': 'e.g., Company Active Directory'}
    )
    entity_id = StringField(
        'Entity ID / Client ID',
        validators=[DataRequired()],
        render_kw={'placeholder': 'SSO Entity ID or OAuth Client ID'}
    )
    sso_url = StringField(
        'SSO URL',
        validators=[DataRequired()],
        render_kw={'placeholder': 'https://sso.company.com/login'}
    )
    certificate = TextAreaField(
        'X.509 Certificate',
        render_kw={
            'placeholder': 'Paste the SSO provider\'s public certificate here',
            'rows': 6
        }
    )
    auto_provision = BooleanField('Auto-provision new users', default=True)
    default_role = SelectField(
        'Default Role for New Users',
        choices=[
            ('employee', 'Employee'),
            ('manager', 'Manager'),
            ('admin', 'Administrator')
        ],
        default='employee'
    )
    is_enabled = BooleanField('Enable SSO', default=False)

class AuditLogFilterForm(FlaskForm):
    """Form for filtering audit logs"""
    user_id = SelectField(
        'User',
        choices=[],
        validators=[Optional()],
        render_kw={'placeholder': 'All Users'}
    )
    action_type = SelectField(
        'Action Type',
        choices=[
            ('', 'All Actions'),
            ('login', 'Login'),
            ('logout', 'Logout'),
            ('create', 'Create'),
            ('update', 'Update'),
            ('delete', 'Delete'),
            ('view', 'View'),
            ('export', 'Export'),
            ('import', 'Import')
        ]
    )
    date_from = StringField(
        'From Date',
        render_kw={'type': 'date'}
    )
    date_to = StringField(
        'To Date',
        render_kw={'type': 'date'}
    )
    resource_type = SelectField(
        'Resource Type',
        choices=[
            ('', 'All Resources'),
            ('user', 'Users'),
            ('company', 'Companies'),
            ('product', 'Products'),
            ('invoice', 'Invoices'),
            ('payment', 'Payments'),
            ('expense', 'Expenses')
        ]
    )
