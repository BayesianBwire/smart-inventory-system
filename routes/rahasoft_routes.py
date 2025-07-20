from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.rahasoft_features import (
    OfflineDataSync, SmartReceiptScanner, BusinessCalendar, VendorRating,
    SMSWhatsAppNotification, BusinessHealthScore, LocalizedTraining,
    TrainingProgress, CommunityGroup, CommunityMembership, CommunityPost
)
from models.more_rahasoft_features import (
    ComplianceAudit, DataBackup, B2BMarketplace, MarketplaceInquiry,
    SmartFundSplitter, PublicPaymentPage, PaymentPageTransaction,
    OnlineMeetingRoom, VoiceCommand, EmergencyFund, EmergencyFundTransaction,
    WellnessTracker, CompanyBadge, AISmartAssistant
)
from datetime import datetime, timedelta
import json
import uuid

rahasoft_bp = Blueprint('rahasoft', __name__, url_prefix='/rahasoft')

# ===== OFFLINE MODE & DATA SYNC =====
@rahasoft_bp.route('/offline-sync')
@login_required
def offline_sync_dashboard():
    """Display offline data sync dashboard"""
    pending_syncs = OfflineDataSync.query.filter_by(
        company_id=current_user.company_id,
        sync_status='pending'
    ).all()
    
    recent_syncs = OfflineDataSync.query.filter_by(
        company_id=current_user.company_id
    ).order_by(OfflineDataSync.created_at.desc()).limit(10).all()
    
    return render_template('rahasoft/offline_sync.html', 
                         pending_syncs=pending_syncs,
                         recent_syncs=recent_syncs)

@rahasoft_bp.route('/sync-data', methods=['POST'])
@login_required
def sync_offline_data():
    """Sync offline data to server"""
    data = request.get_json()
    
    sync_record = OfflineDataSync(
        company_id=current_user.company_id,
        user_id=current_user.id,
        device_id=data.get('device_id'),
        data_type=data.get('data_type'),
        offline_data=data.get('data'),
        sync_status='pending'
    )
    
    db.session.add(sync_record)
    db.session.commit()
    
    # Process sync (simplified for demo)
    sync_record.sync_status = 'synced'
    sync_record.synced_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'status': 'success', 'sync_id': sync_record.id})

# ===== SMART RECEIPTS SCANNER =====
@rahasoft_bp.route('/receipt-scanner')
@login_required
def receipt_scanner():
    """Receipt scanner dashboard"""
    recent_scans = SmartReceiptScanner.query.filter_by(
        company_id=current_user.company_id
    ).order_by(SmartReceiptScanner.created_at.desc()).limit(20).all()
    
    return render_template('rahasoft/receipt_scanner.html', recent_scans=recent_scans)

@rahasoft_bp.route('/scan-receipt', methods=['POST'])
@login_required
def scan_receipt():
    """Process scanned receipt"""
    data = request.get_json()
    
    scan_record = SmartReceiptScanner(
        company_id=current_user.company_id,
        user_id=current_user.id,
        receipt_image_url=data.get('image_url'),
        processing_status='processing'
    )
    
    db.session.add(scan_record)
    db.session.commit()
    
    # Simulate OCR processing (in production, this would call actual OCR service)
    scan_record.extracted_text = "Sample extracted text"
    scan_record.merchant_name = "Sample Merchant"
    scan_record.transaction_amount = 1500.00
    scan_record.mpesa_code = data.get('mpesa_code')
    scan_record.processing_status = 'completed'
    scan_record.processed_at = datetime.utcnow()
    scan_record.confidence_score = 0.95
    
    db.session.commit()
    
    return jsonify({'status': 'success', 'scan_id': scan_record.id})

# ===== BUSINESS CALENDAR =====
@rahasoft_bp.route('/calendar')
@login_required
def business_calendar():
    """Business calendar with Kenyan holidays"""
    events = BusinessCalendar.query.filter_by(
        company_id=current_user.company_id
    ).all()
    
    kenyan_holidays = BusinessCalendar.get_kenyan_holidays()
    
    return render_template('rahasoft/calendar.html', 
                         events=events, 
                         kenyan_holidays=kenyan_holidays)

@rahasoft_bp.route('/calendar/add-event', methods=['POST'])
@login_required
def add_calendar_event():
    """Add new calendar event"""
    data = request.form
    
    event = BusinessCalendar(
        company_id=current_user.company_id,
        title=data.get('title'),
        description=data.get('description'),
        event_type=data.get('event_type'),
        event_date=datetime.strptime(data.get('event_date'), '%Y-%m-%d').date(),
        start_time=datetime.strptime(data.get('start_time'), '%H:%M').time() if data.get('start_time') else None,
        end_time=datetime.strptime(data.get('end_time'), '%H:%M').time() if data.get('end_time') else None,
        is_all_day=bool(data.get('is_all_day')),
        created_by=current_user.id
    )
    
    db.session.add(event)
    db.session.commit()
    
    flash('📅 Event added successfully!', 'success')
    return redirect(url_for('rahasoft.business_calendar'))

# ===== VENDOR RATING SYSTEM =====
@rahasoft_bp.route('/vendor-ratings')
@login_required
def vendor_ratings():
    """Vendor rating and review system"""
    ratings = VendorRating.query.filter_by(
        company_id=current_user.company_id
    ).order_by(VendorRating.created_at.desc()).all()
    
    return render_template('rahasoft/vendor_ratings.html', ratings=ratings)

@rahasoft_bp.route('/rate-vendor', methods=['POST'])
@login_required
def rate_vendor():
    """Submit vendor rating"""
    data = request.form
    
    rating = VendorRating(
        company_id=current_user.company_id,
        vendor_id=data.get('vendor_id'),
        rated_by=current_user.id,
        overall_rating=int(data.get('overall_rating')),
        delivery_rating=int(data.get('delivery_rating', 0)) or None,
        quality_rating=int(data.get('quality_rating', 0)) or None,
        communication_rating=int(data.get('communication_rating', 0)) or None,
        pricing_rating=int(data.get('pricing_rating', 0)) or None,
        review_title=data.get('review_title'),
        review_text=data.get('review_text'),
        order_reference=data.get('order_reference'),
        is_anonymous=bool(data.get('is_anonymous'))
    )
    
    db.session.add(rating)
    db.session.commit()
    
    flash('⭐ Vendor rating submitted successfully!', 'success')
    return redirect(url_for('rahasoft.vendor_ratings'))

# ===== SMS/WHATSAPP NOTIFICATIONS =====
@rahasoft_bp.route('/notifications')
@login_required
def notifications_dashboard():
    """SMS/WhatsApp notifications dashboard"""
    notifications = SMSWhatsAppNotification.query.filter_by(
        company_id=current_user.company_id
    ).order_by(SMSWhatsAppNotification.created_at.desc()).limit(50).all()
    
    return render_template('rahasoft/notifications.html', notifications=notifications)

@rahasoft_bp.route('/send-notification', methods=['POST'])
@login_required
def send_notification():
    """Send SMS/WhatsApp notification"""
    data = request.form
    
    notification = SMSWhatsAppNotification(
        company_id=current_user.company_id,
        recipient_phone=data.get('recipient_phone'),
        recipient_name=data.get('recipient_name'),
        message_type=data.get('message_type'),
        notification_type=data.get('notification_type'),
        subject=data.get('subject'),
        message_content=data.get('message_content'),
        created_by=current_user.id
    )
    
    if data.get('schedule_for'):
        notification.scheduled_for = datetime.strptime(data.get('schedule_for'), '%Y-%m-%dT%H:%M')
        notification.is_scheduled = True
    else:
        # Send immediately (in production, this would call SMS/WhatsApp API)
        notification.status = 'sent'
        notification.sent_at = datetime.utcnow()
    
    db.session.add(notification)
    db.session.commit()
    
    flash('📱 Notification queued successfully!', 'success')
    return redirect(url_for('rahasoft.notifications_dashboard'))

# ===== BUSINESS HEALTH SCORE =====
@rahasoft_bp.route('/health-score')
@login_required
def business_health_score():
    """Business health score dashboard"""
    latest_score = BusinessHealthScore.query.filter_by(
        company_id=current_user.company_id
    ).order_by(BusinessHealthScore.calculation_date.desc()).first()
    
    score_history = BusinessHealthScore.query.filter_by(
        company_id=current_user.company_id
    ).order_by(BusinessHealthScore.calculation_date.desc()).limit(12).all()
    
    return render_template('rahasoft/health_score.html', 
                         latest_score=latest_score,
                         score_history=score_history)

@rahasoft_bp.route('/calculate-health-score', methods=['POST'])
@login_required
def calculate_health_score():
    """Calculate new business health score"""
    # Get calculation results
    results = BusinessHealthScore.calculate_health_score(current_user.company_id)
    
    # Create new score record
    health_score = BusinessHealthScore(
        company_id=current_user.company_id,
        financial_health=results['financial_health'],
        operational_efficiency=results['operational_efficiency'],
        customer_satisfaction=results['customer_satisfaction'],
        inventory_management=results['inventory_management'],
        cash_flow_health=results['cash_flow_health'],
        overall_score=results['overall_score'],
        score_grade=results['score_grade'],
        calculation_date=datetime.utcnow().date(),
        period_start=datetime.utcnow().date() - timedelta(days=30),
        period_end=datetime.utcnow().date()
    )
    
    db.session.add(health_score)
    db.session.commit()
    
    flash(f'📊 Health score calculated: {results["overall_score"]:.1f}% ({results["score_grade"]})', 'success')
    return redirect(url_for('rahasoft.business_health_score'))

# ===== LOCALIZED TRAINING =====
@rahasoft_bp.route('/training')
@login_required
def training_portal():
    """Localized business training portal"""
    available_training = LocalizedTraining.query.filter_by(
        is_active=True,
        language='en'  # Can be made dynamic based on user preference
    ).all()
    
    user_progress = TrainingProgress.query.filter_by(
        user_id=current_user.id
    ).all()
    
    return render_template('rahasoft/training.html', 
                         available_training=available_training,
                         user_progress=user_progress)

@rahasoft_bp.route('/training/<int:training_id>/start')
@login_required
def start_training(training_id):
    """Start or continue training"""
    training = LocalizedTraining.query.get_or_404(training_id)
    
    progress = TrainingProgress.query.filter_by(
        user_id=current_user.id,
        training_id=training_id
    ).first()
    
    if not progress:
        progress = TrainingProgress(
            user_id=current_user.id,
            training_id=training_id,
            company_id=current_user.company_id,
            status='in_progress',
            started_at=datetime.utcnow()
        )
        db.session.add(progress)
        db.session.commit()
    
    progress.last_accessed = datetime.utcnow()
    db.session.commit()
    
    return render_template('rahasoft/training_content.html', 
                         training=training, 
                         progress=progress)

# ===== COMMUNITY GROUPS =====
@rahasoft_bp.route('/community')
@login_required
def community_groups():
    """Industry-specific community groups"""
    my_groups = CommunityMembership.query.filter_by(
        user_id=current_user.id
    ).all()
    
    available_groups = CommunityGroup.query.filter_by(
        is_public=True
    ).limit(20).all()
    
    return render_template('rahasoft/community.html', 
                         my_groups=my_groups,
                         available_groups=available_groups)

@rahasoft_bp.route('/community/<int:group_id>')
@login_required
def community_group_detail(group_id):
    """View community group details and posts"""
    group = CommunityGroup.query.get_or_404(group_id)
    
    membership = CommunityMembership.query.filter_by(
        group_id=group_id,
        user_id=current_user.id
    ).first()
    
    posts = CommunityPost.query.filter_by(
        group_id=group_id
    ).order_by(CommunityPost.created_at.desc()).limit(20).all()
    
    return render_template('rahasoft/community_group.html', 
                         group=group,
                         membership=membership,
                         posts=posts)

@rahasoft_bp.route('/community/<int:group_id>/join', methods=['POST'])
@login_required
def join_community_group(group_id):
    """Join a community group"""
    group = CommunityGroup.query.get_or_404(group_id)
    
    existing_membership = CommunityMembership.query.filter_by(
        group_id=group_id,
        user_id=current_user.id
    ).first()
    
    if existing_membership:
        flash('You are already a member of this group!', 'info')
    else:
        membership = CommunityMembership(
            group_id=group_id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            status='pending' if group.requires_approval else 'active'
        )
        
        db.session.add(membership)
        
        # Update group member count
        group.member_count += 1
        db.session.commit()
        
        status_msg = 'pending approval' if group.requires_approval else 'active'
        flash(f'✅ Successfully joined group! Status: {status_msg}', 'success')
    
    return redirect(url_for('rahasoft.community_group_detail', group_id=group_id))

# ===== COMPLIANCE AUDIT =====
@rahasoft_bp.route('/audit-me')
@login_required
def compliance_audit():
    """Self-compliance checker (Audit Me button)"""
    recent_audits = ComplianceAudit.query.filter_by(
        company_id=current_user.company_id
    ).order_by(ComplianceAudit.audit_date.desc()).limit(10).all()
    
    return render_template('rahasoft/compliance_audit.html', recent_audits=recent_audits)

@rahasoft_bp.route('/run-audit', methods=['POST'])
@login_required
def run_compliance_audit():
    """Run automated compliance audit"""
    audit_type = request.form.get('audit_type', 'full')
    
    # Run the audit
    results = ComplianceAudit.run_auto_audit(current_user.company_id)
    
    # Create audit record
    audit = ComplianceAudit(
        company_id=current_user.company_id,
        audit_type=audit_type,
        audit_scope='full',
        kra_compliance=results['kra_compliance'],
        nssf_compliance=results['nssf_compliance'],
        nhif_compliance=results['nhif_compliance'],
        county_license_status=results['county_license_status'],
        overall_score=results['overall_score'],
        compliance_level=results['compliance_level'],
        critical_issues=results['critical_issues'],
        medium_issues=results['medium_issues'],
        low_issues=results['low_issues'],
        immediate_actions=results['immediate_actions'],
        long_term_actions=results['long_term_actions'],
        audit_date=datetime.utcnow().date(),
        period_start=datetime.utcnow().date() - timedelta(days=90),
        period_end=datetime.utcnow().date(),
        status='completed',
        completed_at=datetime.utcnow()
    )
    
    db.session.add(audit)
    db.session.commit()
    
    flash(f'🔍 Audit completed! Compliance score: {results["overall_score"]:.1f}% ({results["compliance_level"]})', 
          'success' if results['compliance_level'] in ['excellent', 'good'] else 'warning')
    
    return redirect(url_for('rahasoft.compliance_audit'))

# ===== DATA BACKUP =====
@rahasoft_bp.route('/backup')
@login_required
def data_backup():
    """Data backup dashboard"""
    backups = DataBackup.query.filter_by(
        company_id=current_user.company_id
    ).order_by(DataBackup.backup_started.desc()).limit(20).all()
    
    return render_template('rahasoft/backup.html', backups=backups)

@rahasoft_bp.route('/create-backup', methods=['POST'])
@login_required
def create_backup():
    """Create new data backup"""
    data = request.form
    
    backup = DataBackup(
        company_id=current_user.company_id,
        backup_type=data.get('backup_type', 'manual'),
        backup_location=data.get('backup_location'),
        backup_file_name=f"backup_{current_user.company_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip",
        data_types=data.getlist('data_types'),
        status='in_progress',
        created_by=current_user.id
    )
    
    db.session.add(backup)
    db.session.commit()
    
    # Simulate backup process (in production, this would be async)
    backup.status = 'completed'
    backup.backup_completed = datetime.utcnow()
    backup.backup_size = 1024 * 1024 * 5  # 5MB example
    backup.record_count = 1000  # Example count
    
    db.session.commit()
    
    flash('💾 Backup created successfully!', 'success')
    return redirect(url_for('rahasoft.data_backup'))

# ===== API ENDPOINTS FOR MOBILE =====
@rahasoft_bp.route('/api/health-score/<int:company_id>')
@login_required
def api_health_score(company_id):
    """API endpoint for mobile app health score"""
    if current_user.company_id != company_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    latest_score = BusinessHealthScore.query.filter_by(
        company_id=company_id
    ).order_by(BusinessHealthScore.calculation_date.desc()).first()
    
    if latest_score:
        return jsonify({
            'overall_score': float(latest_score.overall_score),
            'grade': latest_score.score_grade,
            'financial_health': float(latest_score.financial_health),
            'operational_efficiency': float(latest_score.operational_efficiency),
            'customer_satisfaction': float(latest_score.customer_satisfaction),
            'calculation_date': latest_score.calculation_date.isoformat()
        })
    
    return jsonify({'error': 'No health score data available'}), 404

@rahasoft_bp.route('/api/notifications/unread-count')
@login_required
def api_unread_notifications():
    """Get count of unread notifications"""
    count = SMSWhatsAppNotification.query.filter_by(
        company_id=current_user.company_id,
        status='pending'
    ).count()
    
    return jsonify({'unread_count': count})
