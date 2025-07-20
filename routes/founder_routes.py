from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import (
    db, Company, User, FounderMetrics, CompanyFeedback, SystemAlert,
    BusinessMetrics, PaymentVerification, EnhancedAuditLog as AuditLog
)
from sqlalchemy import func, desc
from functools import wraps

founder_bp = Blueprint('founder', __name__, url_prefix='/founder')

def founder_required(f):
    """Decorator to ensure only founder can access these routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_founder():
            flash('Access denied. Founder privileges required.', 'error')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

@founder_bp.route('/dashboard')
@login_required
@founder_required
def dashboard():
    """Main founder dashboard"""
    try:
        # Get current metrics
        today_metrics = FounderMetrics.get_or_create_today()
        
        # Calculate real-time metrics
        total_companies = Company.query.count()
        active_companies = Company.query.filter_by(status='active').count()
        suspended_companies = Company.query.filter_by(status='suspended').count()
        blacklisted_companies = Company.query.filter_by(status='blacklisted').count()
        
        # Get recent activity
        recent_companies = Company.query.order_by(Company.created_at.desc()).limit(10).all()
        pending_feedback = CompanyFeedback.query.filter_by(status='open').count()
        critical_alerts = SystemAlert.get_critical_alerts()
        
        # Calculate growth rate
        growth_rate = FounderMetrics.calculate_growth_rate(30)
        
        # Get revenue data (last 30 days)
        thirty_days_ago = datetime.utcnow().date() - timedelta(days=30)
        payment_data = db.session.query(
            PaymentVerification.created_at.label('date'),
            db.func.sum(PaymentVerification.amount).label('total')
        ).filter(
            PaymentVerification.status == 'verified',
            PaymentVerification.created_at >= thirty_days_ago
        ).group_by(
            db.func.date(PaymentVerification.created_at)
        ).all()
        
        return render_template('founder/dashboard.html',
                             total_companies=total_companies,
                             active_companies=active_companies,
                             suspended_companies=suspended_companies,
                             blacklisted_companies=blacklisted_companies,
                             recent_companies=recent_companies,
                             pending_feedback=pending_feedback,
                             critical_alerts=critical_alerts,
                             growth_rate=growth_rate,
                             payment_data=payment_data,
                             today_metrics=today_metrics)
    
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('founder/dashboard.html')

@founder_bp.route('/companies')
@login_required
@founder_required
def companies():
    """Manage all companies"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    search = request.args.get('search', '')
    
    query = Company.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if search:
        query = query.filter(Company.name.ilike(f'%{search}%'))
    
    companies = query.order_by(Company.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('founder/companies.html',
                         companies=companies,
                         status_filter=status_filter,
                         search=search)

@founder_bp.route('/company/<int:company_id>')
@login_required
@founder_required
def company_detail(company_id):
    """View detailed company information"""
    company = Company.query.get_or_404(company_id)
    
    # Get company metrics
    metrics = BusinessMetrics.query.filter_by(company_id=company_id).order_by(
        BusinessMetrics.date.desc()
    ).limit(30).all()
    
    # Get recent payments
    payments = PaymentVerification.query.filter_by(company_id=company_id).order_by(
        PaymentVerification.created_at.desc()
    ).limit(10).all()
    
    # Get audit logs
    audit_logs = AuditLog.query.filter_by(company_id=company_id).order_by(
        AuditLog.created_at.desc()
    ).limit(20).all()
    
    return render_template('founder/company_detail.html',
                         company=company,
                         metrics=metrics,
                         payments=payments,
                         audit_logs=audit_logs)

@founder_bp.route('/company/<int:company_id>/blacklist', methods=['POST'])
@login_required
@founder_required
def blacklist_company(company_id):
    """Blacklist a company"""
    company = Company.query.get_or_404(company_id)
    reason = request.form.get('reason', 'No reason provided')
    
    company.blacklist(reason, current_user.username)
    db.session.commit()
    
    # Log the action
    AuditLog.log_action(
        user_id=current_user.id,
        action='BLACKLIST',
        resource_type='Company',
        resource_id=company_id,
        description=f'Company blacklisted: {reason}',
        company_id=company_id
    )
    db.session.commit()
    
    flash(f'Company "{company.name}" has been blacklisted.', 'success')
    return redirect(url_for('founder.company_detail', company_id=company_id))

@founder_bp.route('/company/<int:company_id>/reactivate', methods=['POST'])
@login_required
@founder_required
def reactivate_company(company_id):
    """Reactivate a company"""
    company = Company.query.get_or_404(company_id)
    
    company.reactivate()
    db.session.commit()
    
    # Log the action
    AuditLog.log_action(
        user_id=current_user.id,
        action='REACTIVATE',
        resource_type='Company',
        resource_id=company_id,
        description='Company reactivated',
        company_id=company_id
    )
    db.session.commit()
    
    flash(f'Company "{company.name}" has been reactivated.', 'success')
    return redirect(url_for('founder.company_detail', company_id=company_id))

@founder_bp.route('/feedback')
@login_required
@founder_required
def feedback():
    """View all company feedback"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    category_filter = request.args.get('category', 'all')
    
    query = CompanyFeedback.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if category_filter != 'all':
        query = query.filter_by(category=category_filter)
    
    feedback_items = query.order_by(CompanyFeedback.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('founder/feedback.html',
                         feedback_items=feedback_items,
                         status_filter=status_filter,
                         category_filter=category_filter)

@founder_bp.route('/feedback/<int:feedback_id>/respond', methods=['POST'])
@login_required
@founder_required
def respond_to_feedback(feedback_id):
    """Respond to company feedback"""
    feedback = CompanyFeedback.query.get_or_404(feedback_id)
    response = request.form.get('response')
    
    if response:
        feedback.respond(response, current_user.full_name)
        db.session.commit()
        
        flash('Response sent successfully.', 'success')
    else:
        flash('Response cannot be empty.', 'error')
    
    return redirect(url_for('founder.feedback'))

@founder_bp.route('/analytics')
@login_required
@founder_required
def analytics():
    """View system analytics"""
    # Get date range
    days = request.args.get('days', 30, type=int)
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)
    
    # Get founder metrics
    metrics = FounderMetrics.query.filter(
        FounderMetrics.date >= start_date,
        FounderMetrics.date <= end_date
    ).order_by(FounderMetrics.date.asc()).all()
    
    # Calculate totals
    total_revenue = sum(m.daily_revenue for m in metrics)
    total_new_companies = sum(m.new_companies for m in metrics)
    avg_daily_logins = sum(m.daily_logins for m in metrics) / len(metrics) if metrics else 0
    
    # Get subscription distribution
    subscription_stats = db.session.query(
        Company.subscription_plan,
        db.func.count(Company.id).label('count')
    ).group_by(Company.subscription_plan).all()
    
    return render_template('founder/analytics.html',
                         metrics=metrics,
                         total_revenue=total_revenue,
                         total_new_companies=total_new_companies,
                         avg_daily_logins=avg_daily_logins,
                         subscription_stats=subscription_stats,
                         days=days)

@founder_bp.route('/payments')
@login_required
@founder_required
def payments():
    """View all payment transactions"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    method_filter = request.args.get('method', 'all')
    
    query = PaymentVerification.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if method_filter != 'all':
        query = query.filter_by(payment_method=method_filter)
    
    payments = query.order_by(PaymentVerification.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Calculate totals
    total_verified = PaymentVerification.query.filter_by(status='verified').count()
    total_pending = PaymentVerification.query.filter_by(status='pending').count()
    total_amount = db.session.query(
        db.func.sum(PaymentVerification.amount)
    ).filter_by(status='verified').scalar() or 0
    
    return render_template('founder/payments.html',
                         payments=payments,
                         status_filter=status_filter,
                         method_filter=method_filter,
                         total_verified=total_verified,
                         total_pending=total_pending,
                         total_amount=total_amount)

@founder_bp.route('/payment/<int:payment_id>/verify', methods=['POST'])
@login_required
@founder_required
def verify_payment(payment_id):
    """Manually verify a payment"""
    payment = PaymentVerification.query.get_or_404(payment_id)
    notes = request.form.get('notes', 'Manually verified by founder')
    
    payment.verify_payment(current_user.id, notes)
    db.session.commit()
    
    # Log the action
    AuditLog.log_action(
        user_id=current_user.id,
        action='VERIFY_PAYMENT',
        resource_type='PaymentVerification',
        resource_id=payment_id,
        description=f'Payment manually verified: {payment.transaction_id}',
        company_id=payment.company_id
    )
    db.session.commit()
    
    flash('Payment verified successfully.', 'success')
    return redirect(url_for('founder.payments'))

@founder_bp.route('/api/metrics')
@login_required
@founder_required
def api_metrics():
    """API endpoint for dashboard metrics"""
    try:
        metrics = {
            'total_companies': Company.query.count(),
            'active_companies': Company.query.filter_by(status='active').count(),
            'total_users': User.query.count(),
            'pending_feedback': CompanyFeedback.query.filter_by(status='open').count(),
            'critical_alerts': len(SystemAlert.get_critical_alerts()),
            'growth_rate': FounderMetrics.calculate_growth_rate(30)
        }
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
