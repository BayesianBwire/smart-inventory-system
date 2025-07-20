from datetime import datetime, timedelta
from extensions import db
from sqlalchemy import func, text
import json

class DocumentTemplate(db.Model):
    """AI-Powered Document Generator Templates"""
    __tablename__ = 'document_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Template details
    template_type = db.Column(db.String(50), nullable=False)  # contract, letter, business_plan, invoice
    template_name = db.Column(db.String(200), nullable=False)
    template_content = db.Column(db.Text, nullable=False)  # Template with placeholders
    
    # AI parameters
    ai_variables = db.Column(db.JSON, nullable=True)  # Variables to be filled by AI
    industry_specific = db.Column(db.Boolean, default=False)
    language = db.Column(db.String(10), default='en')  # en, sw, fr for African languages
    
    # Usage tracking
    usage_count = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime, nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='document_templates')
    creator = db.relationship('User', backref='created_templates')
    
    def generate_document(self, variables_data):
        """Generate document from template with AI assistance"""
        # In a real implementation, this would use AI to fill in the template
        generated_content = self.template_content
        
        # Simple placeholder replacement (would be enhanced with AI)
        for key, value in variables_data.items():
            placeholder = f"{{{key}}}"
            generated_content = generated_content.replace(placeholder, str(value))
        
        # Update usage tracking
        self.usage_count += 1
        self.last_used = datetime.utcnow()
        
        return generated_content


class GeneratedDocument(db.Model):
    """Store AI-generated documents"""
    __tablename__ = 'generated_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('document_templates.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Document details
    document_name = db.Column(db.String(200), nullable=False)
    document_content = db.Column(db.Text, nullable=False)
    document_type = db.Column(db.String(50), nullable=False)
    
    # Metadata
    variables_used = db.Column(db.JSON, nullable=True)
    file_path = db.Column(db.String(500), nullable=True)  # If saved as file
    
    # Status
    is_signed = db.Column(db.Boolean, default=False)
    signature_data = db.Column(db.JSON, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    signed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    template = db.relationship('DocumentTemplate', backref='generated_documents')
    company = db.relationship('Company', backref='generated_documents')
    user = db.relationship('User', backref='generated_documents')


class DebtTracker(db.Model):
    """Debt Follow-Up Assistant for unpaid invoices"""
    __tablename__ = 'debt_tracker'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    customer_id = db.Column(db.Integer, nullable=False)  # Reference to customer
    
    # Invoice details
    invoice_number = db.Column(db.String(100), nullable=False)
    amount_due = db.Column(db.Numeric(12, 2), nullable=False)
    original_amount = db.Column(db.Numeric(12, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    
    # Customer contact info
    customer_name = db.Column(db.String(200), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=True)
    customer_email = db.Column(db.String(200), nullable=True)
    
    # Follow-up tracking
    reminder_level = db.Column(db.Integer, default=0)  # 0=no reminders, 1=gentle, 2=firm, 3=final
    last_reminder_sent = db.Column(db.DateTime, nullable=True)
    next_reminder_date = db.Column(db.DateTime, nullable=True)
    
    # Payment tracking
    status = db.Column(db.String(20), default='overdue')  # overdue, partial_paid, paid, written_off
    payments_received = db.Column(db.JSON, nullable=True)  # Track partial payments
    
    # Escalation
    escalated_to_legal = db.Column(db.Boolean, default=False)
    escalation_date = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='debt_tracking')
    
    def add_payment(self, amount, payment_method='cash', reference=None):
        """Record a partial payment"""
        if not self.payments_received:
            self.payments_received = []
        
        payment = {
            'amount': float(amount),
            'method': payment_method,
            'reference': reference,
            'date': datetime.utcnow().isoformat()
        }
        
        payments = self.payments_received or []
        payments.append(payment)
        self.payments_received = payments
        
        # Update amount due
        self.amount_due -= amount
        
        # Update status
        if self.amount_due <= 0:
            self.status = 'paid'
        elif self.amount_due < self.original_amount:
            self.status = 'partial_paid'
    
    def escalate_reminder(self):
        """Escalate to next reminder level"""
        if self.reminder_level < 3:
            self.reminder_level += 1
            self.last_reminder_sent = datetime.utcnow()
            
            # Set next reminder date based on level
            if self.reminder_level == 1:
                self.next_reminder_date = datetime.utcnow() + timedelta(days=7)
            elif self.reminder_level == 2:
                self.next_reminder_date = datetime.utcnow() + timedelta(days=3)
            elif self.reminder_level == 3:
                self.next_reminder_date = datetime.utcnow() + timedelta(days=1)
        else:
            # Final escalation to legal
            self.escalated_to_legal = True
            self.escalation_date = datetime.utcnow()


class VoiceNote(db.Model):
    """Instant Voice Notes to Tasks/Reminders"""
    __tablename__ = 'voice_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Voice note details
    audio_file_path = db.Column(db.String(500), nullable=True)
    transcribed_text = db.Column(db.Text, nullable=True)
    original_duration = db.Column(db.Integer, nullable=True)  # in seconds
    
    # AI-extracted information
    task_title = db.Column(db.String(200), nullable=True)
    task_description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    
    # Task conversion
    converted_to_task = db.Column(db.Boolean, default=False)
    task_id = db.Column(db.Integer, nullable=True)  # Reference to created task
    
    # Processing status
    processing_status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    ai_confidence = db.Column(db.Float, nullable=True)  # 0.0 to 1.0
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='voice_notes')
    company = db.relationship('Company', backref='voice_notes')
    
    def process_voice_note(self):
        """Process voice note with AI to extract task information"""
        # In a real implementation, this would use speech-to-text and NLP
        # For now, we'll simulate the processing
        self.processing_status = 'processing'
        
        # Simulated AI processing
        if self.transcribed_text:
            # Extract task information (simplified)
            self.task_title = f"Task from voice note {self.id}"
            self.task_description = self.transcribed_text
            self.ai_confidence = 0.85
            self.processing_status = 'completed'
            self.processed_at = datetime.utcnow()
        else:
            self.processing_status = 'failed'


class TeamVoting(db.Model):
    """Built-In Voting System for Teams"""
    __tablename__ = 'team_voting'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Voting details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    voting_type = db.Column(db.String(30), default='simple')  # simple, ranked, weighted
    
    # Options
    voting_options = db.Column(db.JSON, nullable=False)  # List of options to vote on
    
    # Participants
    eligible_voters = db.Column(db.JSON, nullable=True)  # List of user IDs who can vote
    anonymous_voting = db.Column(db.Boolean, default=False)
    
    # Timing
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    
    # Status
    status = db.Column(db.String(20), default='active')  # active, closed, cancelled
    min_votes_required = db.Column(db.Integer, default=1)
    
    # Results
    results = db.Column(db.JSON, nullable=True)
    winner_option = db.Column(db.String(200), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    closed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    company = db.relationship('Company', backref='team_votes')
    creator = db.relationship('User', backref='created_votes')
    
    def add_vote(self, user_id, option_selected, weight=1):
        """Add a vote from a user"""
        if self.status != 'active' or datetime.utcnow() > self.end_date:
            return False, "Voting is closed"
        
        if self.eligible_voters and user_id not in self.eligible_voters:
            return False, "User not eligible to vote"
        
        # Store vote (this would be in a separate votes table in production)
        vote_data = {
            'user_id': user_id,
            'option': option_selected,
            'weight': weight,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return True, "Vote recorded successfully"
    
    def close_voting(self):
        """Close voting and calculate results"""
        self.status = 'closed'
        self.closed_at = datetime.utcnow()
        
        # Calculate results (simplified)
        self.results = {
            'total_votes': 0,
            'option_counts': {},
            'winner': None
        }


class BusinessMilestone(db.Model):
    """Business Milestone Tracker"""
    __tablename__ = 'business_milestones'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Milestone details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False)  # revenue, staff, customers, products
    
    # Target metrics
    target_value = db.Column(db.Numeric(15, 2), nullable=False)
    current_value = db.Column(db.Numeric(15, 2), default=0)
    unit = db.Column(db.String(20), nullable=True)  # KES, employees, customers, etc.
    
    # Timeline
    target_date = db.Column(db.Date, nullable=True)
    achieved_date = db.Column(db.Date, nullable=True)
    
    # Progress tracking
    progress_percentage = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='in_progress')  # in_progress, achieved, overdue, cancelled
    
    # Celebration
    celebration_planned = db.Column(db.Boolean, default=False)
    reward_amount = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='business_milestones')
    creator = db.relationship('User', backref='created_milestones')
    
    def update_progress(self, new_value):
        """Update milestone progress"""
        self.current_value = new_value
        
        if self.target_value > 0:
            self.progress_percentage = min(100.0, (float(new_value) / float(self.target_value)) * 100)
        
        if self.progress_percentage >= 100.0 and self.status == 'in_progress':
            self.status = 'achieved'
            self.achieved_date = datetime.utcnow().date()
    
    def check_if_overdue(self):
        """Check if milestone is overdue"""
        if (self.target_date and 
            datetime.utcnow().date() > self.target_date and 
            self.status == 'in_progress'):
            self.status = 'overdue'
