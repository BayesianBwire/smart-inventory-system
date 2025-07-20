from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from extensions import db
from models.more_rahasoft_features import (
    B2BMarketplace, MarketplaceInquiry, SmartFundSplitter, PublicPaymentPage,
    PaymentPageTransaction, OnlineMeetingRoom, VoiceCommand, EmergencyFund,
    EmergencyFundTransaction, WellnessTracker, CompanyBadge, AISmartAssistant
)
from datetime import datetime, timedelta
import uuid
import secrets

advanced_bp = Blueprint('advanced', __name__, url_prefix='/advanced')

# ===== B2B MARKETPLACE =====
@advanced_bp.route('/marketplace')
@login_required
def b2b_marketplace():
    """Built-in B2B marketplace"""
    my_listings = B2BMarketplace.query.filter_by(
        company_id=current_user.company_id
    ).order_by(B2BMarketplace.created_at.desc()).all()
    
    all_listings = B2BMarketplace.query.filter(
        B2BMarketplace.status == 'active',
        B2BMarketplace.company_id != current_user.company_id
    ).order_by(B2BMarketplace.created_at.desc()).limit(20).all()
    
    return render_template('advanced/marketplace.html', 
                         my_listings=my_listings,
                         all_listings=all_listings)

@advanced_bp.route('/marketplace/create-listing', methods=['GET', 'POST'])
@login_required
def create_marketplace_listing():
    """Create new marketplace listing"""
    if request.method == 'POST':
        data = request.form
        
        listing = B2BMarketplace(
            company_id=current_user.company_id,
            listing_type=data.get('listing_type'),
            title=data.get('title'),
            description=data.get('description'),
            category=data.get('category'),
            subcategory=data.get('subcategory'),
            keywords=data.get('keywords', '').split(','),
            quantity_needed=int(data.get('quantity_needed')) if data.get('quantity_needed') else None,
            unit_price_range=data.get('unit_price_range'),
            location_preference=data.get('location_preference'),
            minimum_order_quantity=int(data.get('minimum_order_quantity')) if data.get('minimum_order_quantity') else None,
            quality_standards=data.get('quality_standards'),
            delivery_requirements=data.get('delivery_requirements'),
            payment_terms=data.get('payment_terms'),
            contact_person=data.get('contact_person'),
            contact_phone=data.get('contact_phone'),
            contact_email=data.get('contact_email'),
            valid_until=datetime.strptime(data.get('valid_until'), '%Y-%m-%d').date() if data.get('valid_until') else None
        )
        
        db.session.add(listing)
        db.session.commit()
        
        flash('🏪 Marketplace listing created successfully!', 'success')
        return redirect(url_for('advanced.b2b_marketplace'))
    
    return render_template('advanced/create_listing.html')

@advanced_bp.route('/marketplace/<int:listing_id>/inquire', methods=['POST'])
@login_required
def marketplace_inquire(listing_id):
    """Send inquiry about marketplace listing"""
    listing = B2BMarketplace.query.get_or_404(listing_id)
    
    if listing.company_id == current_user.company_id:
        flash('You cannot inquire about your own listing!', 'warning')
        return redirect(url_for('advanced.b2b_marketplace'))
    
    inquiry = MarketplaceInquiry(
        listing_id=listing_id,
        inquirer_company_id=current_user.company_id,
        message=request.form.get('message'),
        inquiry_type=request.form.get('inquiry_type', 'general')
    )
    
    db.session.add(inquiry)
    
    # Update listing inquiry count
    listing.inquiries_count += 1
    db.session.commit()
    
    flash('📩 Inquiry sent successfully!', 'success')
    return redirect(url_for('advanced.b2b_marketplace'))

# ===== SMART FUND SPLITTER =====
@advanced_bp.route('/fund-splitter')
@login_required
def fund_splitter():
    """Smart fund splitter dashboard"""
    budgets = SmartFundSplitter.query.filter_by(
        company_id=current_user.company_id
    ).order_by(SmartFundSplitter.created_at.desc()).all()
    
    active_budget = SmartFundSplitter.query.filter_by(
        company_id=current_user.company_id,
        is_active=True
    ).first()
    
    return render_template('advanced/fund_splitter.html', 
                         budgets=budgets,
                         active_budget=active_budget)

@advanced_bp.route('/fund-splitter/create', methods=['GET', 'POST'])
@login_required
def create_fund_splitter():
    """Create new budget splitter"""
    if request.method == 'POST':
        data = request.form
        
        splitter = SmartFundSplitter(
            company_id=current_user.company_id,
            budget_name=data.get('budget_name'),
            total_income=float(data.get('total_income')),
            operating_expenses_pct=float(data.get('operating_expenses_pct', 0)),
            salaries_pct=float(data.get('salaries_pct', 0)),
            inventory_pct=float(data.get('inventory_pct', 0)),
            marketing_pct=float(data.get('marketing_pct', 0)),
            emergency_fund_pct=float(data.get('emergency_fund_pct', 0)),
            savings_pct=float(data.get('savings_pct', 0)),
            taxes_pct=float(data.get('taxes_pct', 0)),
            other_pct=float(data.get('other_pct', 0)),
            auto_split_enabled=bool(data.get('auto_split_enabled')),
            created_by=current_user.id
        )
        
        # Calculate amounts
        splitter.calculate_amounts()
        
        db.session.add(splitter)
        db.session.commit()
        
        flash('💰 Fund splitter created successfully!', 'success')
        return redirect(url_for('advanced.fund_splitter'))
    
    return render_template('advanced/create_fund_splitter.html')

# ===== PUBLIC PAYMENT PAGE =====
@advanced_bp.route('/payment-pages')
@login_required
def payment_pages():
    """Public 'Pay Me' pages dashboard"""
    pages = PublicPaymentPage.query.filter_by(
        company_id=current_user.company_id
    ).order_by(PublicPaymentPage.created_at.desc()).all()
    
    return render_template('advanced/payment_pages.html', pages=pages)

@advanced_bp.route('/payment-pages/create', methods=['GET', 'POST'])
@login_required
def create_payment_page():
    """Create new public payment page"""
    if request.method == 'POST':
        data = request.form
        
        # Generate unique slug
        base_slug = data.get('page_name').lower().replace(' ', '-').replace('_', '-')
        slug = base_slug
        counter = 1
        while PublicPaymentPage.query.filter_by(page_slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        page = PublicPaymentPage(
            company_id=current_user.company_id,
            page_name=data.get('page_name'),
            page_slug=slug,
            description=data.get('description'),
            accepts_mpesa=bool(data.get('accepts_mpesa')),
            accepts_paypal=bool(data.get('accepts_paypal')),
            accepts_bank_transfer=bool(data.get('accepts_bank_transfer')),
            fixed_amount=float(data.get('fixed_amount')) if data.get('fixed_amount') else None,
            allows_custom_amount=bool(data.get('allows_custom_amount')),
            minimum_amount=float(data.get('minimum_amount', 0)),
            maximum_amount=float(data.get('maximum_amount')) if data.get('maximum_amount') else None,
            theme_color=data.get('theme_color', '#36585C'),
            success_message=data.get('success_message'),
            collect_customer_name=bool(data.get('collect_customer_name')),
            collect_customer_email=bool(data.get('collect_customer_email')),
            collect_customer_phone=bool(data.get('collect_customer_phone')),
            collect_payment_reason=bool(data.get('collect_payment_reason')),
            created_by=current_user.id
        )
        
        db.session.add(page)
        db.session.commit()
        
        flash(f'💳 Payment page created! URL: /pay/{slug}', 'success')
        return redirect(url_for('advanced.payment_pages'))
    
    return render_template('advanced/create_payment_page.html')

@advanced_bp.route('/pay/<slug>')
def public_payment_page(slug):
    """Public payment page (no login required)"""
    page = PublicPaymentPage.query.filter_by(page_slug=slug, is_active=True).first_or_404()
    
    # Increment page views
    page.page_views += 1
    db.session.commit()
    
    return render_template('advanced/public_payment.html', page=page)

@advanced_bp.route('/pay/<slug>/process', methods=['POST'])
def process_payment(slug):
    """Process payment from public page"""
    page = PublicPaymentPage.query.filter_by(page_slug=slug, is_active=True).first_or_404()
    data = request.form
    
    # Generate unique transaction reference
    transaction_ref = f"TXN_{secrets.token_hex(8).upper()}"
    
    transaction = PaymentPageTransaction(
        payment_page_id=page.id,
        customer_name=data.get('customer_name'),
        customer_email=data.get('customer_email'),
        customer_phone=data.get('customer_phone'),
        payment_reason=data.get('payment_reason'),
        amount=float(data.get('amount')),
        payment_method=data.get('payment_method'),
        transaction_reference=transaction_ref,
        status='pending'
    )
    
    db.session.add(transaction)
    
    # Update page stats
    page.total_payments += 1
    page.total_amount_received += float(data.get('amount'))
    db.session.commit()
    
    # In production, integrate with actual payment APIs
    if data.get('payment_method') == 'mpesa':
        # Integrate with M-Pesa STK Push
        pass
    elif data.get('payment_method') == 'paypal':
        # Integrate with PayPal
        pass
    
    # For demo, mark as completed
    transaction.status = 'completed'
    transaction.payment_date = datetime.utcnow()
    transaction.external_reference = f"MPESA_{secrets.token_hex(6).upper()}"
    db.session.commit()
    
    return render_template('advanced/payment_success.html', 
                         transaction=transaction, 
                         page=page)

# ===== ONLINE MEETING ROOM =====
@advanced_bp.route('/meeting-rooms')
@login_required
def meeting_rooms():
    """Online meeting rooms dashboard"""
    rooms = OnlineMeetingRoom.query.filter_by(
        company_id=current_user.company_id
    ).order_by(OnlineMeetingRoom.created_at.desc()).all()
    
    return render_template('advanced/meeting_rooms.html', rooms=rooms)

@advanced_bp.route('/meeting-rooms/create', methods=['POST'])
@login_required
def create_meeting_room():
    """Create new meeting room"""
    data = request.form
    
    # Generate unique room ID
    room_id = f"room_{secrets.token_hex(6)}"
    
    room = OnlineMeetingRoom(
        company_id=current_user.company_id,
        room_name=data.get('room_name'),
        room_id=room_id,
        room_password=data.get('room_password') if data.get('requires_password') else None,
        max_participants=int(data.get('max_participants', 10)),
        requires_password=bool(data.get('requires_password')),
        waiting_room_enabled=bool(data.get('waiting_room_enabled')),
        recording_enabled=bool(data.get('recording_enabled')),
        host_user_id=current_user.id,
        join_url=f"https://meet.rahasoft.com/join/{room_id}",
        start_url=f"https://meet.rahasoft.com/host/{room_id}"
    )
    
    db.session.add(room)
    db.session.commit()
    
    flash(f'📹 Meeting room created! Room ID: {room_id}', 'success')
    return redirect(url_for('advanced.meeting_rooms'))

# ===== VOICE COMMANDS =====
@advanced_bp.route('/voice-commands')
@login_required
def voice_commands():
    """Voice commands dashboard"""
    commands = VoiceCommand.query.filter_by(
        company_id=current_user.company_id,
        user_id=current_user.id
    ).order_by(VoiceCommand.created_at.desc()).limit(50).all()
    
    return render_template('advanced/voice_commands.html', commands=commands)

@advanced_bp.route('/voice-commands/process', methods=['POST'])
@login_required
def process_voice_command():
    """Process voice command"""
    data = request.get_json()
    
    command = VoiceCommand(
        company_id=current_user.company_id,
        user_id=current_user.id,
        transcribed_text=data.get('transcribed_text'),
        confidence_score=data.get('confidence_score', 0.0),
        status='processing'
    )
    
    db.session.add(command)
    db.session.commit()
    
    # Simulate AI processing
    text = data.get('transcribed_text', '').lower()
    
    if 'create invoice' in text or 'new invoice' in text:
        command.command_type = 'create_invoice'
        command.intent = 'invoice_creation'
        command.action_performed = 'invoice_created'
        command.created_record_type = 'invoice'
    elif 'add task' in text or 'new task' in text:
        command.command_type = 'add_task'
        command.intent = 'task_creation'
        command.action_performed = 'task_created'
        command.created_record_type = 'task'
    elif 'record sale' in text or 'new sale' in text:
        command.command_type = 'record_sale'
        command.intent = 'sale_recording'
        command.action_performed = 'sale_recorded'
        command.created_record_type = 'sale'
    
    command.status = 'completed'
    command.processed_at = datetime.utcnow()
    command.processing_time = 0.5
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'command_id': command.id,
        'action_performed': command.action_performed,
        'message': f'Command processed: {command.command_type}'
    })

# ===== EMERGENCY FUND =====
@advanced_bp.route('/emergency-fund')
@login_required
def emergency_fund():
    """Emergency fund tracker"""
    funds = EmergencyFund.query.filter_by(
        company_id=current_user.company_id
    ).order_by(EmergencyFund.created_at.desc()).all()
    
    active_fund = EmergencyFund.query.filter_by(
        company_id=current_user.company_id,
        is_active=True
    ).first()
    
    recent_transactions = []
    if active_fund:
        recent_transactions = EmergencyFundTransaction.query.filter_by(
            emergency_fund_id=active_fund.id
        ).order_by(EmergencyFundTransaction.created_at.desc()).limit(10).all()
    
    return render_template('advanced/emergency_fund.html', 
                         funds=funds,
                         active_fund=active_fund,
                         recent_transactions=recent_transactions)

@advanced_bp.route('/emergency-fund/create', methods=['POST'])
@login_required
def create_emergency_fund():
    """Create new emergency fund"""
    data = request.form
    
    fund = EmergencyFund(
        company_id=current_user.company_id,
        fund_name=data.get('fund_name'),
        target_amount=float(data.get('target_amount')),
        auto_contribution_enabled=bool(data.get('auto_contribution_enabled')),
        contribution_percentage=float(data.get('contribution_percentage', 0)),
        low_balance_threshold=float(data.get('low_balance_threshold', 0)),
        created_by=current_user.id
    )
    
    db.session.add(fund)
    db.session.commit()
    
    flash('🚨 Emergency fund created successfully!', 'success')
    return redirect(url_for('advanced.emergency_fund'))

@advanced_bp.route('/emergency-fund/<int:fund_id>/transaction', methods=['POST'])
@login_required
def emergency_fund_transaction(fund_id):
    """Add contribution or withdrawal to emergency fund"""
    fund = EmergencyFund.query.get_or_404(fund_id)
    
    if fund.company_id != current_user.company_id:
        abort(403)
    
    data = request.form
    transaction_type = data.get('transaction_type')
    amount = float(data.get('amount'))
    
    transaction = EmergencyFundTransaction(
        emergency_fund_id=fund_id,
        transaction_type=transaction_type,
        amount=amount,
        reason=data.get('reason'),
        created_by=current_user.id
    )
    
    # Update fund balance
    if transaction_type == 'contribution':
        fund.current_amount += amount
        fund.last_contribution = datetime.utcnow()
    elif transaction_type == 'withdrawal':
        if fund.current_amount >= amount:
            fund.current_amount -= amount
            fund.last_withdrawal = datetime.utcnow()
        else:
            flash('❌ Insufficient funds for withdrawal!', 'error')
            return redirect(url_for('advanced.emergency_fund'))
    
    db.session.add(transaction)
    db.session.commit()
    
    action = 'added to' if transaction_type == 'contribution' else 'withdrawn from'
    flash(f'💰 KES {amount:,.2f} {action} emergency fund successfully!', 'success')
    return redirect(url_for('advanced.emergency_fund'))

# ===== WELLNESS TRACKER =====
@advanced_bp.route('/wellness')
@login_required
def wellness_tracker():
    """Staff wellness and mood tracker"""
    # Get wellness data for current user
    recent_entries = WellnessTracker.query.filter_by(
        user_id=current_user.id
    ).order_by(WellnessTracker.date.desc()).limit(30).all()
    
    # Company-wide wellness summary (for managers)
    company_summary = None
    if current_user.role in ['admin', 'manager']:
        company_summary = db.session.query(
            db.func.avg(WellnessTracker.mood_rating),
            db.func.avg(WellnessTracker.stress_level),
            db.func.avg(WellnessTracker.energy_level),
            db.func.avg(WellnessTracker.job_satisfaction)
        ).filter(
            WellnessTracker.company_id == current_user.company_id,
            WellnessTracker.date >= datetime.utcnow().date() - timedelta(days=30)
        ).first()
    
    return render_template('advanced/wellness.html', 
                         recent_entries=recent_entries,
                         company_summary=company_summary)

@advanced_bp.route('/wellness/submit', methods=['POST'])
@login_required
def submit_wellness():
    """Submit daily wellness data"""
    data = request.form
    today = datetime.utcnow().date()
    
    # Check if already submitted today
    existing = WellnessTracker.query.filter_by(
        user_id=current_user.id,
        date=today
    ).first()
    
    if existing:
        flash('You have already submitted wellness data for today!', 'info')
        return redirect(url_for('advanced.wellness_tracker'))
    
    wellness = WellnessTracker(
        company_id=current_user.company_id,
        employee_id=current_user.employee_id if hasattr(current_user, 'employee_id') else None,
        user_id=current_user.id,
        date=today,
        mood_rating=int(data.get('mood_rating')) if data.get('mood_rating') else None,
        stress_level=int(data.get('stress_level')) if data.get('stress_level') else None,
        energy_level=int(data.get('energy_level')) if data.get('energy_level') else None,
        job_satisfaction=int(data.get('job_satisfaction')) if data.get('job_satisfaction') else None,
        work_life_balance=int(data.get('work_life_balance')) if data.get('work_life_balance') else None,
        team_collaboration=int(data.get('team_collaboration')) if data.get('team_collaboration') else None,
        feedback=data.get('feedback'),
        concerns=data.get('concerns'),
        suggestions=data.get('suggestions'),
        hours_slept=float(data.get('hours_slept')) if data.get('hours_slept') else None,
        sick_day=bool(data.get('sick_day')),
        taking_breaks=bool(data.get('taking_breaks')),
        is_anonymous=bool(data.get('is_anonymous')),
        share_with_manager=bool(data.get('share_with_manager'))
    )
    
    db.session.add(wellness)
    db.session.commit()
    
    flash('✅ Wellness data submitted successfully!', 'success')
    return redirect(url_for('advanced.wellness_tracker'))

# ===== COMPANY BADGES =====
@advanced_bp.route('/badges')
@login_required
def company_badges():
    """Company badge system"""
    badges = CompanyBadge.query.filter_by(
        company_id=current_user.company_id
    ).order_by(CompanyBadge.earned_date.desc()).all()
    
    return render_template('advanced/badges.html', badges=badges)

@advanced_bp.route('/badges/check', methods=['POST'])
@login_required
def check_badges():
    """Check for new badges to award"""
    new_badges = CompanyBadge.check_and_award_badges(current_user.company_id)
    
    if new_badges:
        for badge in new_badges:
            db.session.add(badge)
        db.session.commit()
        
        flash(f'🏆 Congratulations! You earned {len(new_badges)} new badge(s)!', 'success')
    else:
        flash('No new badges available at this time. Keep up the good work!', 'info')
    
    return redirect(url_for('advanced.company_badges'))

# ===== AI SMART ASSISTANT =====
@advanced_bp.route('/ai-assistant')
@login_required
def ai_assistant():
    """AI smart assistant for daily tasks"""
    recent_conversations = AISmartAssistant.query.filter_by(
        company_id=current_user.company_id,
        user_id=current_user.id
    ).order_by(AISmartAssistant.created_at.desc()).limit(20).all()
    
    return render_template('advanced/ai_assistant.html', 
                         recent_conversations=recent_conversations)

@advanced_bp.route('/ai-assistant/chat', methods=['POST'])
@login_required
def ai_assistant_chat():
    """Process AI assistant message"""
    data = request.get_json()
    message = data.get('message', '')
    session_id = data.get('session_id') or str(uuid.uuid4())
    
    # Log user message
    user_message = AISmartAssistant(
        company_id=current_user.company_id,
        user_id=current_user.id,
        session_id=session_id,
        message_type='user_query',
        message_content=message
    )
    
    db.session.add(user_message)
    
    # Generate AI response (simplified for demo)
    response_content = generate_ai_response(message)
    
    # Log AI response
    ai_response = AISmartAssistant(
        company_id=current_user.company_id,
        user_id=current_user.id,
        session_id=session_id,
        message_type='assistant_response',
        message_content=response_content,
        response_time=0.5
    )
    
    db.session.add(ai_response)
    db.session.commit()
    
    return jsonify({
        'response': response_content,
        'session_id': session_id,
        'message_id': ai_response.id
    })

def generate_ai_response(message):
    """Generate AI response (simplified)"""
    message_lower = message.lower()
    
    if 'inventory' in message_lower:
        return "I can help you manage your inventory. Would you like to check stock levels, add new products, or view low stock alerts?"
    elif 'sales' in message_lower:
        return "Let me help with sales data. I can show you recent sales, generate reports, or help you record a new sale."
    elif 'report' in message_lower:
        return "I can generate various reports for you: sales reports, inventory reports, financial summaries, or employee reports. Which would you like?"
    elif 'customer' in message_lower:
        return "I can help with customer management. Would you like to add a new customer, view customer details, or check customer payment history?"
    elif 'help' in message_lower:
        return "I'm here to help! I can assist with inventory management, sales tracking, report generation, customer management, and much more. What would you like to do?"
    else:
        return "I understand you're asking about your business. Could you be more specific? I can help with inventory, sales, customers, reports, and many other tasks."

# ===== API ENDPOINTS =====
@advanced_bp.route('/api/emergency-fund/status')
@login_required
def api_emergency_fund_status():
    """API endpoint for emergency fund status"""
    fund = EmergencyFund.query.filter_by(
        company_id=current_user.company_id,
        is_active=True
    ).first()
    
    if fund:
        return jsonify({
            'fund_name': fund.fund_name,
            'current_amount': float(fund.current_amount),
            'target_amount': float(fund.target_amount),
            'completion_percentage': fund.completion_percentage,
            'last_contribution': fund.last_contribution.isoformat() if fund.last_contribution else None
        })
    
    return jsonify({'error': 'No active emergency fund'}), 404

@advanced_bp.route('/api/wellness/summary')
@login_required
def api_wellness_summary():
    """API endpoint for wellness summary"""
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    summary = db.session.query(
        db.func.avg(WellnessTracker.mood_rating),
        db.func.avg(WellnessTracker.stress_level),
        db.func.avg(WellnessTracker.job_satisfaction),
        db.func.count(WellnessTracker.id)
    ).filter(
        WellnessTracker.company_id == current_user.company_id,
        WellnessTracker.date >= datetime.utcnow().date() - timedelta(days=7)
    ).first()
    
    return jsonify({
        'avg_mood': float(summary[0]) if summary[0] else 0,
        'avg_stress': float(summary[1]) if summary[1] else 0,
        'avg_satisfaction': float(summary[2]) if summary[2] else 0,
        'total_entries': int(summary[3]) if summary[3] else 0
    })
