from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import (
    db, DocumentTemplate, GeneratedDocument, DebtTracker, VoiceNote,
    TeamVoting, BusinessMilestone, PayrollAutomation, PriceRecommendation,
    QRInvoice, MicroInvestor, CustomerFeedbackHeatmap
)
import json
import qrcode
import io
import base64

ai_features_bp = Blueprint('ai_features', __name__, url_prefix='/ai')

@ai_features_bp.route('/dashboard')
@login_required
def ai_dashboard():
    """AI Features Dashboard"""
    company_id = current_user.company_id
    
    # Get AI features usage statistics
    document_templates = DocumentTemplate.query.filter_by(company_id=company_id, is_active=True).count()
    voice_notes_today = VoiceNote.query.filter(
        VoiceNote.company_id == company_id,
        VoiceNote.created_at >= datetime.utcnow().date()
    ).count()
    
    active_votes = TeamVoting.query.filter_by(company_id=company_id, status='active').count()
    overdue_debts = DebtTracker.query.filter_by(company_id=company_id, status='overdue').count()
    
    return render_template('ai_features/dashboard.html',
                         document_templates=document_templates,
                         voice_notes_today=voice_notes_today,
                         active_votes=active_votes,
                         overdue_debts=overdue_debts)

# Document Generator Routes
@ai_features_bp.route('/documents')
@login_required
def document_templates():
    """List document templates"""
    templates = DocumentTemplate.query.filter_by(
        company_id=current_user.company_id,
        is_active=True
    ).all()
    return render_template('ai_features/document_templates.html', templates=templates)

@ai_features_bp.route('/documents/create', methods=['GET', 'POST'])
@login_required
def create_document_template():
    """Create new document template"""
    if request.method == 'POST':
        template = DocumentTemplate(
            company_id=current_user.company_id,
            template_type=request.form['template_type'],
            template_name=request.form['template_name'],
            template_content=request.form['template_content'],
            created_by=current_user.id,
            language=request.form.get('language', 'en')
        )
        
        # Parse AI variables from template content
        ai_variables = []
        content = request.form['template_content']
        # Simple extraction of variables in {variable_name} format
        import re
        variables = re.findall(r'\{(\w+)\}', content)
        template.ai_variables = [{'name': var, 'type': 'text'} for var in variables]
        
        db.session.add(template)
        db.session.commit()
        
        flash('Document template created successfully!', 'success')
        return redirect(url_for('ai_features.document_templates'))
    
    return render_template('ai_features/create_document_template.html')

@ai_features_bp.route('/documents/generate/<int:template_id>', methods=['GET', 'POST'])
@login_required
def generate_document(template_id):
    """Generate document from template"""
    template = DocumentTemplate.query.get_or_404(template_id)
    
    if template.company_id != current_user.company_id:
        flash('Access denied', 'error')
        return redirect(url_for('ai_features.document_templates'))
    
    if request.method == 'POST':
        # Get variables from form
        variables_data = {}
        for key, value in request.form.items():
            if key.startswith('var_'):
                variable_name = key[4:]  # Remove 'var_' prefix
                variables_data[variable_name] = value
        
        # Generate document
        generated_content = template.generate_document(variables_data)
        
        # Save generated document
        document = GeneratedDocument(
            template_id=template.id,
            company_id=current_user.company_id,
            user_id=current_user.id,
            document_name=request.form['document_name'],
            document_content=generated_content,
            document_type=template.template_type,
            variables_used=variables_data
        )
        
        db.session.add(document)
        db.session.commit()
        
        flash('Document generated successfully!', 'success')
        return redirect(url_for('ai_features.view_generated_document', doc_id=document.id))
    
    return render_template('ai_features/generate_document.html', template=template)

@ai_features_bp.route('/documents/generated/<int:doc_id>')
@login_required
def view_generated_document(doc_id):
    """View generated document"""
    document = GeneratedDocument.query.get_or_404(doc_id)
    
    if document.company_id != current_user.company_id:
        flash('Access denied', 'error')
        return redirect(url_for('ai_features.document_templates'))
    
    return render_template('ai_features/view_document.html', document=document)

# Voice Notes Routes
@ai_features_bp.route('/voice-notes')
@login_required
def voice_notes():
    """List voice notes"""
    notes = VoiceNote.query.filter_by(
        company_id=current_user.company_id
    ).order_by(VoiceNote.created_at.desc()).all()
    
    return render_template('ai_features/voice_notes.html', notes=notes)

@ai_features_bp.route('/voice-notes/create', methods=['POST'])
@login_required
def create_voice_note():
    """Create voice note (simulated - would handle audio upload)"""
    # In production, this would handle audio file upload and processing
    transcribed_text = request.form.get('transcribed_text', '')
    
    voice_note = VoiceNote(
        user_id=current_user.id,
        company_id=current_user.company_id,
        transcribed_text=transcribed_text,
        original_duration=60  # Simulated duration
    )
    
    # Process the voice note
    voice_note.process_voice_note()
    
    db.session.add(voice_note)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'note_id': voice_note.id,
        'task_title': voice_note.task_title
    })

# Team Voting Routes
@ai_features_bp.route('/voting')
@login_required
def team_voting():
    """List team votes"""
    votes = TeamVoting.query.filter_by(company_id=current_user.company_id).all()
    return render_template('ai_features/team_voting.html', votes=votes)

@ai_features_bp.route('/voting/create', methods=['GET', 'POST'])
@login_required
def create_vote():
    """Create new team vote"""
    if request.method == 'POST':
        options = request.form.getlist('options')
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
        
        vote = TeamVoting(
            company_id=current_user.company_id,
            created_by=current_user.id,
            title=request.form['title'],
            description=request.form['description'],
            voting_options=options,
            end_date=end_date,
            anonymous_voting=bool(request.form.get('anonymous'))
        )
        
        db.session.add(vote)
        db.session.commit()
        
        flash('Vote created successfully!', 'success')
        return redirect(url_for('ai_features.team_voting'))
    
    return render_template('ai_features/create_vote.html')

# Business Milestones Routes
@ai_features_bp.route('/milestones')
@login_required
def business_milestones():
    """List business milestones"""
    milestones = BusinessMilestone.query.filter_by(
        company_id=current_user.company_id
    ).order_by(BusinessMilestone.target_date.asc()).all()
    
    return render_template('ai_features/milestones.html', milestones=milestones)

@ai_features_bp.route('/milestones/create', methods=['GET', 'POST'])
@login_required
def create_milestone():
    """Create new business milestone"""
    if request.method == 'POST':
        milestone = BusinessMilestone(
            company_id=current_user.company_id,
            created_by=current_user.id,
            title=request.form['title'],
            description=request.form['description'],
            category=request.form['category'],
            target_value=float(request.form['target_value']),
            unit=request.form['unit'],
            target_date=datetime.strptime(request.form['target_date'], '%Y-%m-%d').date()
        )
        
        db.session.add(milestone)
        db.session.commit()
        
        flash('Milestone created successfully!', 'success')
        return redirect(url_for('ai_features.business_milestones'))
    
    return render_template('ai_features/create_milestone.html')

@ai_features_bp.route('/milestones/<int:milestone_id>/update', methods=['POST'])
@login_required
def update_milestone_progress(milestone_id):
    """Update milestone progress"""
    milestone = BusinessMilestone.query.get_or_404(milestone_id)
    
    if milestone.company_id != current_user.company_id:
        return jsonify({'success': False, 'error': 'Access denied'})
    
    new_value = float(request.form['current_value'])
    milestone.update_progress(new_value)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'progress_percentage': milestone.progress_percentage,
        'status': milestone.status
    })

# QR Invoice Routes
@ai_features_bp.route('/qr-invoices')
@login_required
def qr_invoices():
    """List QR invoices"""
    invoices = QRInvoice.query.filter_by(company_id=current_user.company_id).all()
    return render_template('ai_features/qr_invoices.html', invoices=invoices)

@ai_features_bp.route('/qr-invoices/create', methods=['GET', 'POST'])
@login_required
def create_qr_invoice():
    """Create QR code invoice"""
    if request.method == 'POST':
        # Generate unique invoice number
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{current_user.company_id}-{datetime.now().microsecond}"
        
        invoice = QRInvoice(
            company_id=current_user.company_id,
            invoice_number=invoice_number,
            customer_name=request.form['customer_name'],
            customer_phone=request.form.get('customer_phone'),
            customer_email=request.form.get('customer_email'),
            amount=float(request.form['amount']),
            currency=request.form.get('currency', 'KES'),
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        # Generate QR code
        qr_data = invoice.generate_qr_code()
        
        # Create QR code image (in production, save to file system)
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)
        
        # Convert to base64 for display
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        
        db.session.add(invoice)
        db.session.commit()
        
        return render_template('ai_features/qr_invoice_created.html', 
                             invoice=invoice, qr_image=img_str)
    
    return render_template('ai_features/create_qr_invoice.html')

# Debt Tracking Routes
@ai_features_bp.route('/debt-tracker')
@login_required
def debt_tracker():
    """Debt tracking dashboard"""
    overdue_debts = DebtTracker.query.filter_by(
        company_id=current_user.company_id,
        status='overdue'
    ).all()
    
    total_overdue = sum(debt.amount_due for debt in overdue_debts)
    
    return render_template('ai_features/debt_tracker.html',
                         overdue_debts=overdue_debts,
                         total_overdue=total_overdue)

@ai_features_bp.route('/debt-tracker/<int:debt_id>/escalate', methods=['POST'])
@login_required
def escalate_debt_reminder(debt_id):
    """Escalate debt reminder"""
    debt = DebtTracker.query.get_or_404(debt_id)
    
    if debt.company_id != current_user.company_id:
        return jsonify({'success': False, 'error': 'Access denied'})
    
    debt.escalate_reminder()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'reminder_level': debt.reminder_level,
        'next_reminder_date': debt.next_reminder_date.isoformat() if debt.next_reminder_date else None
    })

# Customer Feedback Heatmap
@ai_features_bp.route('/feedback-heatmap')
@login_required
def feedback_heatmap():
    """Customer feedback heatmap"""
    heatmap_data = CustomerFeedbackHeatmap.get_heatmap_data(current_user.company_id)
    
    return render_template('ai_features/feedback_heatmap.html',
                         heatmap_data=heatmap_data)

@ai_features_bp.route('/api/heatmap-data')
@login_required
def api_heatmap_data():
    """API endpoint for heatmap data"""
    days = request.args.get('days', 30, type=int)
    heatmap_data = CustomerFeedbackHeatmap.get_heatmap_data(current_user.company_id, days)
    
    return jsonify(heatmap_data)
