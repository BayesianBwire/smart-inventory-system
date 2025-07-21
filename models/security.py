"""
Two-Factor Authentication implementation for RahaSoft ERP
Supports TOTP (Time-based One-Time Password) using Google Authenticator
"""
import pyotp
import qrcode
import io
import base64
import secrets
import string
from datetime import datetime, timedelta
from extensions import db
from sqlalchemy import JSON


class TwoFactorAuth(db.Model):
    """Two-Factor Authentication model"""
    __tablename__ = 'two_factor_auth'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, unique=True)  # Remove FK for test
    
    # TOTP Secret
    secret_key = db.Column(db.String(32), nullable=False)
    
    # Backup Codes
    backup_codes = db.Column(JSON, default=list)
    
    # Status
    is_enabled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.regenerate_secret()
    
    def regenerate_secret(self):
        """Generate new TOTP secret"""
        self.secret_key = pyotp.random_base32()
    
    def get_qr_code_url(self, user_email, issuer_name):
        """Generate QR code URL for TOTP setup"""
        totp = pyotp.TOTP(self.secret_key)
        return totp.provisioning_uri(
            name=user_email,
            issuer_name=issuer_name
        )
    
    def get_qr_code_image(self, user_email, issuer_name):
        """Generate QR code image as base64"""
        totp_uri = self.get_qr_code_url(user_email, issuer_name)
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for HTML display
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    
    def verify_token(self, token):
        """Verify TOTP token"""
        totp = pyotp.TOTP(self.secret_key)
        if totp.verify(token, valid_window=1):  # Allow 30 seconds window
            self.last_used = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    def verify_backup_code(self, code):
        """Verify and consume backup code"""
        if code in self.backup_codes:
            self.backup_codes.remove(code)
            self.last_used = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    def generate_backup_codes(self, count=10):
        """Generate new backup codes"""
        codes = []
        for _ in range(count):
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            codes.append(code)
        
        self.backup_codes = codes
        db.session.commit()
        return codes
    
    def get_unused_backup_codes(self):
        """Get list of unused backup codes"""
        return self.backup_codes or []
    
    def enable(self):
        """Enable 2FA for user"""
        self.is_enabled = True
        db.session.commit()
    
    def disable(self):
        """Disable 2FA for user"""
        self.is_enabled = False
        db.session.commit()
    
    @classmethod
    def generate_for_user(cls, user_id):
        """Generate 2FA setup for a user"""
        # Check if user already has 2FA
        existing = cls.query.filter_by(user_id=user_id).first()
        if existing:
            return existing
        
        # Create new 2FA record
        two_factor = cls(user_id=user_id)
        
        db.session.add(two_factor)
        db.session.commit()
        
        return two_factor

    @property
    def secret(self):
        """Alias for secret_key for compatibility"""
        return self.secret_key


class LoginAttempt(db.Model):
    """Track login attempts for security"""
    __tablename__ = 'login_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)  # Remove FK for test
    company_id = db.Column(db.Integer, nullable=True)  # Remove FK for test
    
    # Attempt Details
    ip_address = db.Column(db.String(45))  # IPv6 support
    user_agent = db.Column(db.Text)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Result
    successful = db.Column(db.Boolean, default=False)
    failure_reason = db.Column(db.String(100))  # invalid_password, account_locked, etc.
    
    # 2FA Details
    required_2fa = db.Column(db.Boolean, default=False)
    used_2fa = db.Column(db.Boolean, default=False)
    used_backup_code = db.Column(db.Boolean, default=False)


class SecuritySettings(db.Model):
    """Company-wide security settings"""
    __tablename__ = 'security_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, nullable=False, unique=True)  # Remove FK for test
    
    # 2FA Settings
    require_2fa = db.Column(db.Boolean, default=False)
    enforce_2fa_for_admins = db.Column(db.Boolean, default=True)
    
    # Password Policy
    password_min_length = db.Column(db.Integer, default=8)
    password_require_uppercase = db.Column(db.Boolean, default=True)
    password_require_lowercase = db.Column(db.Boolean, default=True)
    password_require_numbers = db.Column(db.Boolean, default=True)
    password_require_special = db.Column(db.Boolean, default=True)
    password_history_count = db.Column(db.Integer, default=5)  # Remember last N passwords
    password_max_age_days = db.Column(db.Integer, default=90)
    
    # Session Management
    session_timeout_minutes = db.Column(db.Integer, default=30)
    concurrent_sessions_limit = db.Column(db.Integer, default=3)
    
    # Login Security
    max_login_attempts = db.Column(db.Integer, default=5)
    lockout_duration_minutes = db.Column(db.Integer, default=30)
    
    # IP Restrictions
    allowed_ip_ranges = db.Column(JSON, default=list)  # CIDR notation
    blocked_ip_ranges = db.Column(JSON, default=list)
    
    # API Security
    api_rate_limit_per_hour = db.Column(db.Integer, default=1000)
    api_rate_limit_per_day = db.Column(db.Integer, default=10000)
    
    # Audit Settings
    log_all_actions = db.Column(db.Boolean, default=True)
    log_retention_days = db.Column(db.Integer, default=365)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, nullable=True)  # Remove FK for test
    
    @classmethod
    def get_company_settings(cls, company_id):
        """Get security settings for company, create if not exists"""
        settings = cls.query.filter_by(company_id=company_id).first()
        if not settings:
            settings = cls(company_id=company_id)
            db.session.add(settings)
            db.session.commit()
        return settings


class SecurityUtils:
    """Utility functions for security operations"""
    
    @staticmethod
    def check_password_strength(password):
        """Check password strength and return score"""
        score = 0
        feedback = []
        
        # Length check
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("Password should be at least 8 characters long")
        
        if len(password) >= 12:
            score += 1
        
        # Character type checks
        if any(c.isupper() for c in password):
            score += 1
        else:
            feedback.append("Add uppercase letters")
        
        if any(c.islower() for c in password):
            score += 1
        else:
            feedback.append("Add lowercase letters")
        
        if any(c.isdigit() for c in password):
            score += 1
        else:
            feedback.append("Add numbers")
        
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 1
        else:
            feedback.append("Add special characters")
        
        # Common patterns check
        common_patterns = ['123', 'abc', 'password', 'admin', 'user']
        if any(pattern in password.lower() for pattern in common_patterns):
            score -= 1
            feedback.append("Avoid common patterns")
        
        # Strength levels
        if score <= 2:
            strength = "Very Weak"
            color = "danger"
        elif score <= 3:
            strength = "Weak"
            color = "warning"
        elif score <= 4:
            strength = "Fair"
            color = "info"
        elif score <= 5:
            strength = "Strong"
            color = "success"
        else:
            strength = "Very Strong"
            color = "success"
        
        return {
            'score': score,
            'max_score': 6,
            'strength': strength,
            'color': color,
            'feedback': feedback,
            'percentage': min(100, (score / 6) * 100)
        }
    
    @staticmethod
    def check_password_breach(password):
        """Check if password appears in known breaches using k-anonymity"""
        import hashlib
        import requests
        
        try:
            # Hash password with SHA-1
            sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
            
            # Use k-anonymity: send only first 5 characters
            prefix = sha1_hash[:5]
            suffix = sha1_hash[5:]
            
            # Query HaveIBeenPwned API
            response = requests.get(
                f"https://api.pwnedpasswords.com/range/{prefix}",
                timeout=5
            )
            
            if response.status_code == 200:
                # Check if suffix appears in response
                for line in response.text.splitlines():
                    hash_suffix, count = line.split(':')
                    if hash_suffix == suffix:
                        return True  # Password found in breach
            
            return False  # Password not found in breaches
            
        except Exception:
            # If API call fails, assume password is safe
            return False
    
    @staticmethod
    def generate_secure_token(length=32):
        """Generate cryptographically secure random token"""
        return secrets.token_urlsafe(length)
