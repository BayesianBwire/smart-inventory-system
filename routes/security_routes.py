"""
Security Routes for RahaSoft ERP
Handles Two-Factor Authentication, Password Security, and Enterprise Security Features
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import qrcode
import io
import base64
from urllib.parse import quote

from forms.security_forms import (
    TwoFactorSetupForm, TwoFactorVerificationForm, TwoFactorDisableForm,
    SecuritySettingsForm, PasswordChangeForm, APIKeyForm, SingleSignOnForm,
    AuditLogFilterForm
)
from models.security import TwoFactorAuth, LoginAttempt, SecuritySettings, SecurityUtils
from models.user import User
from models.company import Company
from extensions import db
from utils.cache_manager import CacheInvalidator

security_bp = Blueprint('security', __name__, url_prefix='/security')


@security_bp.route('/dashboard')
@login_required
def security_dashboard():
    """Security dashboard with overview"""
    user_2fa = TwoFactorAuth.query.filter_by(user_id=current_user.id).first()
    
    # Get security settings for company
    security_settings = SecuritySettings.get_company_settings(current_user.company_id)
    
    # Recent login attempts
    recent_attempts = LoginAttempt.query.filter_by(
        user_id=current_user.id
    ).order_by(LoginAttempt.attempted_at.desc()).limit(10).all()
    
    # Security metrics
    failed_attempts_today = LoginAttempt.query.filter(
        LoginAttempt.user_id == current_user.id,
        LoginAttempt.successful == False,
        LoginAttempt.attempted_at >= datetime.utcnow().date()
    ).count()
    
    context = {
        'user_2fa': user_2fa,
        'security_settings': security_settings,
        'recent_attempts': recent_attempts,
        'failed_attempts_today': failed_attempts_today,
        'password_strength': SecurityUtils.check_password_strength(current_user.password_hash)
    }
    
    return render_template('security/dashboard.html', **context)


# Two-Factor Authentication Routes
@security_bp.route('/2fa/setup', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    """Set up Two-Factor Authentication"""
    # Check if 2FA is already enabled
    existing_2fa = TwoFactorAuth.query.filter_by(user_id=current_user.id).first()
    if existing_2fa and existing_2fa.is_enabled:
        flash('Two-Factor Authentication is already enabled for your account.', 'info')
        return redirect(url_for('security.security_dashboard'))
    
    form = TwoFactorSetupForm()
    
    if form.validate_on_submit():
        # Generate new secret if not exists
        if not existing_2fa:
            two_factor = TwoFactorAuth.generate_for_user(current_user.id)
        else:
            two_factor = existing_2fa
            two_factor.regenerate_secret()
        
        # Verify the provided token
        if two_factor.verify_token(form.token.data):
            # Generate backup codes
            backup_codes = two_factor.generate_backup_codes()
            two_factor.enable()
            
            flash('Two-Factor Authentication has been enabled successfully!', 'success')
            
            # Show backup codes to user
            return render_template('security/backup_codes.html', 
                                 backup_codes=backup_codes)
        else:
            flash('Invalid verification code. Please try again.', 'error')
    
    # Generate QR code for setup
    if not existing_2fa:
        two_factor = TwoFactorAuth.generate_for_user(current_user.id)
    else:
        two_factor = existing_2fa
    
    # Generate QR code
    qr_code_url = two_factor.get_qr_code_url(
        current_user.email,
        current_app.config.get('COMPANY_NAME', 'RahaSoft ERP')
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_code_url)
    qr.make(fit=True)
    
    # Create QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for display
    img_buffer = io.BytesIO()
    qr_img.save(img_buffer, format='PNG')
    qr_code_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    
    return render_template('security/setup_2fa.html', 
                         form=form, 
                         qr_code=qr_code_base64,
                         manual_key=two_factor.secret)


@security_bp.route('/2fa/verify', methods=['GET', 'POST'])
@login_required
def verify_2fa():
    """Verify 2FA token for sensitive operations"""
    form = TwoFactorVerificationForm()
    
    if form.validate_on_submit():
        two_factor = TwoFactorAuth.query.filter_by(user_id=current_user.id).first()
        
        if not two_factor or not two_factor.is_enabled:
            flash('Two-Factor Authentication is not enabled.', 'error')
            return redirect(url_for('security.security_dashboard'))
        
        if two_factor.verify_token(form.token.data):
            # Store verification in session for current operation
            session['2fa_verified'] = True
            session['2fa_verified_at'] = datetime.utcnow().isoformat()
            
            flash('2FA verification successful.', 'success')
            
            # Redirect to intended page or dashboard
            next_page = request.args.get('next')
            return redirect(next_page or url_for('security.security_dashboard'))
        else:
            flash('Invalid verification code.', 'error')
    
    return render_template('security/verify_2fa.html', form=form)


@security_bp.route('/2fa/disable', methods=['GET', 'POST'])
@login_required
def disable_2fa():
    """Disable Two-Factor Authentication"""
    two_factor = TwoFactorAuth.query.filter_by(user_id=current_user.id).first()
    
    if not two_factor or not two_factor.is_enabled:
        flash('Two-Factor Authentication is not enabled.', 'info')
        return redirect(url_for('security.security_dashboard'))
    
    form = TwoFactorDisableForm()
    
    if form.validate_on_submit():
        # Verify current password
        if not current_user.check_password(form.current_password.data):
            flash('Incorrect current password.', 'error')
            return render_template('security/disable_2fa.html', form=form)
        
        # Verify 2FA token
        if not two_factor.verify_token(form.token.data):
            flash('Invalid verification code.', 'error')
            return render_template('security/disable_2fa.html', form=form)
        
        # Disable 2FA
        two_factor.disable()
        flash('Two-Factor Authentication has been disabled.', 'success')
        
        return redirect(url_for('security.security_dashboard'))
    
    return render_template('security/disable_2fa.html', form=form)


@security_bp.route('/2fa/backup-codes')
@login_required
def view_backup_codes():
    """View remaining backup codes"""
    two_factor = TwoFactorAuth.query.filter_by(user_id=current_user.id).first()
    
    if not two_factor or not two_factor.is_enabled:
        flash('Two-Factor Authentication is not enabled.', 'error')
        return redirect(url_for('security.security_dashboard'))
    
    return render_template('security/backup_codes.html', 
                         backup_codes=two_factor.get_unused_backup_codes())


@security_bp.route('/2fa/regenerate-backup-codes', methods=['POST'])
@login_required
def regenerate_backup_codes():
    """Regenerate backup codes"""
    two_factor = TwoFactorAuth.query.filter_by(user_id=current_user.id).first()
    
    if not two_factor or not two_factor.is_enabled:
        flash('Two-Factor Authentication is not enabled.', 'error')
        return redirect(url_for('security.security_dashboard'))
    
    # Require 2FA verification for this sensitive operation
    if not session.get('2fa_verified'):
        return redirect(url_for('security.verify_2fa', next=request.url))
    
    # Generate new backup codes
    backup_codes = two_factor.generate_backup_codes()
    flash('Backup codes have been regenerated. Please save them securely.', 'success')
    
    return render_template('security/backup_codes.html', backup_codes=backup_codes)


# Password Management Routes
@security_bp.route('/password/change', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    form = PasswordChangeForm()
    
    if form.validate_on_submit():
        # Verify current password
        if not current_user.check_password(form.current_password.data):
            flash('Incorrect current password.', 'error')
            return render_template('security/change_password.html', form=form)
        
        # Check new password strength
        strength = SecurityUtils.check_password_strength(form.new_password.data)
        if strength['score'] < 3:  # Require strong passwords
            flash('Password is too weak. Please use a stronger password.', 'error')
            return render_template('security/change_password.html', form=form, password_strength=strength)
        
        # Update password
        current_user.set_password(form.new_password.data)
        current_user.password_changed_at = datetime.utcnow()
        db.session.commit()
        
        # Invalidate user cache
        CacheInvalidator.invalidate_user_cache(current_user.id)
        
        flash('Password changed successfully.', 'success')
        return redirect(url_for('security.security_dashboard'))
    
    return render_template('security/change_password.html', form=form)


@security_bp.route('/password/strength-check', methods=['POST'])
@login_required
def check_password_strength():
    """AJAX endpoint to check password strength"""
    password = request.json.get('password', '')
    strength = SecurityUtils.check_password_strength(password)
    return jsonify(strength)


# Security Settings Routes (Admin only)
@security_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def security_settings():
    """Company-wide security settings (Admin only)"""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('security.security_dashboard'))
    
    settings = SecuritySettings.get_company_settings(current_user.company_id)
    form = SecuritySettingsForm(obj=settings)
    
    if form.validate_on_submit():
        # Update or create security settings
        if not settings:
            settings = SecuritySettings(company_id=current_user.company_id)
        
        form.populate_obj(settings)
        settings.updated_by = current_user.id
        settings.updated_at = datetime.utcnow()
        
        db.session.add(settings)
        db.session.commit()
        
        flash('Security settings updated successfully.', 'success')
        return redirect(url_for('security.security_settings'))
    
    return render_template('security/settings.html', form=form, settings=settings)


# API Key Management Routes
@security_bp.route('/api-keys')
@login_required
def api_keys():
    """Manage API keys"""
    from models.api_framework import APIKey
    
    user_keys = APIKey.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).all()
    
    return render_template('security/api_keys.html', api_keys=user_keys)


@security_bp.route('/api-keys/create', methods=['GET', 'POST'])
@login_required
def create_api_key():
    """Create new API key"""
    form = APIKeyForm()
    
    if form.validate_on_submit():
        from models.api_framework import APIKey
        
        # Generate API key
        api_key, key_record = APIKey.generate_key(
            company_id=current_user.company_id,
            user_id=current_user.id,
            name=form.name.data,
            permissions=form.permissions.data,
            expires_in_days=form.expires_in_days.data or 90
        )
        
        flash('API key created successfully. Please copy it now - you won\'t see it again!', 'success')
        
        return render_template('security/api_key_created.html', 
                             api_key=api_key, 
                             key_record=key_record)
    
    return render_template('security/create_api_key.html', form=form)


@security_bp.route('/api-keys/<int:key_id>/revoke', methods=['POST'])
@login_required
def revoke_api_key(key_id):
    """Revoke API key"""
    from models.api_framework import APIKey
    
    api_key = APIKey.query.filter_by(
        id=key_id,
        user_id=current_user.id
    ).first()
    
    if not api_key:
        flash('API key not found.', 'error')
        return redirect(url_for('security.api_keys'))
    
    api_key.revoke()
    flash('API key revoked successfully.', 'success')
    
    return redirect(url_for('security.api_keys'))


# Single Sign-On Configuration (Admin only)
@security_bp.route('/sso', methods=['GET', 'POST'])
@login_required
def sso_config():
    """Configure Single Sign-On (Admin only)"""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('security.security_dashboard'))
    
    form = SingleSignOnForm()
    
    if form.validate_on_submit():
        # Store SSO configuration in company settings
        # This is a placeholder - actual SSO implementation would be more complex
        flash('SSO configuration saved. Implementation in progress.', 'info')
        return redirect(url_for('security.sso_config'))
    
    return render_template('security/sso_config.html', form=form)


# Audit Log Routes
@security_bp.route('/audit-log')
@login_required
def audit_log():
    """View security audit log"""
    if current_user.role not in ['admin', 'manager']:
        flash('Access denied. Manager privileges required.', 'error')
        return redirect(url_for('security.security_dashboard'))
    
    form = AuditLogFilterForm()
    
    # Base query
    query = LoginAttempt.query.filter_by(company_id=current_user.company_id)
    
    # Apply filters if form is submitted
    if form.validate_on_submit():
        if form.user_id.data:
            query = query.filter(LoginAttempt.user_id == form.user_id.data)
        
        if form.from_date.data:
            query = query.filter(LoginAttempt.attempted_at >= form.from_date.data)
        
        if form.to_date.data:
            query = query.filter(LoginAttempt.attempted_at <= form.to_date.data)
        
        if form.success_only.data:
            query = query.filter(LoginAttempt.successful == True)
        
        if form.failures_only.data:
            query = query.filter(LoginAttempt.successful == False)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    login_attempts = query.order_by(
        LoginAttempt.attempted_at.desc()
    ).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    return render_template('security/audit_log.html', 
                         form=form, 
                         login_attempts=login_attempts)


# Security Utilities
@security_bp.route('/check-breach', methods=['POST'])
@login_required
def check_password_breach():
    """Check if password has been breached (AJAX)"""
    password = request.json.get('password', '')
    is_breached = SecurityUtils.check_password_breach(password)
    
    return jsonify({
        'breached': is_breached,
        'message': 'This password has been found in data breaches. Please choose a different password.' if is_breached else 'Password looks good!'
    })


# Helper functions for templates
@security_bp.context_processor
def security_context():
    """Add security-related context to templates"""
    def is_2fa_enabled():
        if not current_user.is_authenticated:
            return False
        two_factor = TwoFactorAuth.query.filter_by(user_id=current_user.id).first()
        return two_factor and two_factor.is_enabled
    
    def requires_2fa_verification():
        """Check if current operation requires 2FA verification"""
        return not session.get('2fa_verified', False)
    
    def get_password_age():
        """Get days since password was last changed"""
        if not current_user.is_authenticated or not current_user.password_changed_at:
            return None
        return (datetime.utcnow() - current_user.password_changed_at).days
    
    return {
        'is_2fa_enabled': is_2fa_enabled,
        'requires_2fa_verification': requires_2fa_verification,
        'get_password_age': get_password_age
    }
