from datetime import datetime, timedelta
from extensions import db
from sqlalchemy import func
import json

class ComplianceAudit(db.Model):
    __tablename__ = 'compliance_audits'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Audit details
    audit_type = db.Column(db.String(50), nullable=False)  # tax, financial, operational, legal
    audit_scope = db.Column(db.String(100), nullable=False)  # full, partial, specific
    
    # Kenya-specific compliance
    kra_compliance = db.Column(db.Boolean, default=False)
    nssf_compliance = db.Column(db.Boolean, default=False)
    nhif_compliance = db.Column(db.Boolean, default=False)
    county_license_status = db.Column(db.String(20), default='unknown')
    
    # Audit results
    overall_score = db.Column(db.Float, default=0.0)  # 0-100
    compliance_level = db.Column(db.String(20), default='poor')  # excellent, good, fair, poor
    
    # Issues found
    critical_issues = db.Column(db.JSON, nullable=True)
    medium_issues = db.Column(db.JSON, nullable=True)
    low_issues = db.Column(db.JSON, nullable=True)
    
    # Recommendations
    immediate_actions = db.Column(db.JSON, nullable=True)
    long_term_actions = db.Column(db.JSON, nullable=True)
    
    # Audit metadata
    audit_date = db.Column(db.Date, nullable=False)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    
    # Status
    status = db.Column(db.String(20), default='in_progress')  # scheduled, in_progress, completed
    auto_generated = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    company = db.relationship('Company', backref='compliance_audits')
    
    def __repr__(self):
        return f"<ComplianceAudit {self.audit_type} for company {self.company_id} ({self.compliance_level})>"
    
    @classmethod
    def run_auto_audit(cls, company_id):
        """Run automatic compliance audit for a company"""
        # This would contain logic to check various compliance requirements
        audit_results = {
            'kra_compliance': True,
            'nssf_compliance': False,
            'nhif_compliance': True,
            'county_license_status': 'valid',
            'overall_score': 75.0,
            'compliance_level': 'good',
            'critical_issues': ['NSSF contributions not up to date'],
            'medium_issues': ['Missing some receipts for Q2'],
            'low_issues': ['Invoice numbering could be improved'],
            'immediate_actions': ['Update NSSF payments'],
            'long_term_actions': ['Implement better record keeping system']
        }
        
        return audit_results


class DataBackup(db.Model):
    __tablename__ = 'data_backups'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Backup details
    backup_type = db.Column(db.String(50), nullable=False)  # full, incremental, manual
    backup_location = db.Column(db.String(50), nullable=False)  # local_phone, usb, cloud
    backup_size = db.Column(db.BigInteger, nullable=True)  # in bytes
    
    # File details
    backup_file_name = db.Column(db.String(200), nullable=False)
    backup_file_path = db.Column(db.String(500), nullable=True)
    file_hash = db.Column(db.String(64), nullable=True)  # For integrity check
    
    # Backup content
    data_types = db.Column(db.JSON, nullable=False)  # ['inventory', 'sales', 'customers', etc.]
    record_count = db.Column(db.Integer, default=0)
    
    # Status and metadata
    status = db.Column(db.String(20), default='in_progress')  # in_progress, completed, failed, corrupted
    compression_used = db.Column(db.Boolean, default=True)
    encryption_used = db.Column(db.Boolean, default=True)
    
    # Timing
    backup_started = db.Column(db.DateTime, default=datetime.utcnow)
    backup_completed = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)
    
    # Error handling
    error_message = db.Column(db.Text, nullable=True)
    retry_count = db.Column(db.Integer, default=0)
    
    # Auto-backup settings
    is_scheduled = db.Column(db.Boolean, default=False)
    schedule_frequency = db.Column(db.String(20), nullable=True)  # daily, weekly, monthly
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    company = db.relationship('Company', backref='data_backups')
    creator = db.relationship('User', backref='initiated_backups')
    
    def __repr__(self):
        return f"<DataBackup {self.backup_type} to {self.backup_location} ({self.status})>"


class B2BMarketplace(db.Model):
    __tablename__ = 'b2b_marketplace'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Listing details
    listing_type = db.Column(db.String(50), nullable=False)  # seeking_supplier, offering_product, seeking_buyer
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Product/Service details
    category = db.Column(db.String(100), nullable=False)
    subcategory = db.Column(db.String(100), nullable=True)
    keywords = db.Column(db.JSON, nullable=True)
    
    # Business details
    quantity_needed = db.Column(db.Integer, nullable=True)
    unit_price_range = db.Column(db.String(100), nullable=True)
    location_preference = db.Column(db.String(100), nullable=True)
    
    # Requirements
    minimum_order_quantity = db.Column(db.Integer, nullable=True)
    quality_standards = db.Column(db.Text, nullable=True)
    delivery_requirements = db.Column(db.Text, nullable=True)
    payment_terms = db.Column(db.String(200), nullable=True)
    
    # Contact and visibility
    contact_person = db.Column(db.String(200), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    contact_email = db.Column(db.String(200), nullable=True)
    is_public = db.Column(db.Boolean, default=True)
    
    # Status and metrics
    status = db.Column(db.String(20), default='active')  # active, paused, closed, expired
    views_count = db.Column(db.Integer, default=0)
    inquiries_count = db.Column(db.Integer, default=0)
    responses_count = db.Column(db.Integer, default=0)
    
    # Dates
    valid_until = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='marketplace_listings')
    
    def __repr__(self):
        return f"<B2BMarketplace {self.listing_type}: {self.title}>"


class MarketplaceInquiry(db.Model):
    __tablename__ = 'marketplace_inquiries'
    
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('b2b_marketplace.id'), nullable=False)
    inquirer_company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Inquiry details
    message = db.Column(db.Text, nullable=False)
    inquiry_type = db.Column(db.String(50), default='general')  # general, quote_request, partnership
    
    # Response
    response = db.Column(db.Text, nullable=True)
    response_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, responded, closed
    
    # Follow-up
    follow_up_scheduled = db.Column(db.Boolean, default=False)
    follow_up_date = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    listing = db.relationship('B2BMarketplace', backref='inquiries')
    inquirer_company = db.relationship('Company', backref='marketplace_inquiries')
    
    def __repr__(self):
        return f"<MarketplaceInquiry for listing {self.listing_id} from company {self.inquirer_company_id}>"


class SmartFundSplitter(db.Model):
    __tablename__ = 'smart_fund_splitter'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Budget configuration
    budget_name = db.Column(db.String(200), nullable=False)
    total_income = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Allocation percentages
    operating_expenses_pct = db.Column(db.Float, default=0.0)
    salaries_pct = db.Column(db.Float, default=0.0)
    inventory_pct = db.Column(db.Float, default=0.0)
    marketing_pct = db.Column(db.Float, default=0.0)
    emergency_fund_pct = db.Column(db.Float, default=0.0)
    savings_pct = db.Column(db.Float, default=0.0)
    taxes_pct = db.Column(db.Float, default=0.0)
    other_pct = db.Column(db.Float, default=0.0)
    
    # Calculated amounts
    operating_expenses_amount = db.Column(db.Numeric(10, 2), default=0)
    salaries_amount = db.Column(db.Numeric(10, 2), default=0)
    inventory_amount = db.Column(db.Numeric(10, 2), default=0)
    marketing_amount = db.Column(db.Numeric(10, 2), default=0)
    emergency_fund_amount = db.Column(db.Numeric(10, 2), default=0)
    savings_amount = db.Column(db.Numeric(10, 2), default=0)
    taxes_amount = db.Column(db.Numeric(10, 2), default=0)
    other_amount = db.Column(db.Numeric(10, 2), default=0)
    
    # Auto-split settings
    auto_split_enabled = db.Column(db.Boolean, default=False)
    split_frequency = db.Column(db.String(20), default='monthly')  # daily, weekly, monthly
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    last_split_date = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    company = db.relationship('Company', backref='fund_splitters')
    creator = db.relationship('User', backref='created_budgets')
    
    def __repr__(self):
        return f"<SmartFundSplitter {self.budget_name} for company {self.company_id}>"
    
    def calculate_amounts(self):
        """Calculate actual amounts based on percentages"""
        total = float(self.total_income)
        
        self.operating_expenses_amount = total * (self.operating_expenses_pct / 100)
        self.salaries_amount = total * (self.salaries_pct / 100)
        self.inventory_amount = total * (self.inventory_pct / 100)
        self.marketing_amount = total * (self.marketing_pct / 100)
        self.emergency_fund_amount = total * (self.emergency_fund_pct / 100)
        self.savings_amount = total * (self.savings_pct / 100)
        self.taxes_amount = total * (self.taxes_pct / 100)
        self.other_amount = total * (self.other_pct / 100)


class PublicPaymentPage(db.Model):
    __tablename__ = 'public_payment_pages'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Page details
    page_name = db.Column(db.String(200), nullable=False)
    page_slug = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    
    # Payment configuration
    accepts_mpesa = db.Column(db.Boolean, default=True)
    accepts_paypal = db.Column(db.Boolean, default=False)
    accepts_bank_transfer = db.Column(db.Boolean, default=False)
    
    # Amount settings
    fixed_amount = db.Column(db.Numeric(10, 2), nullable=True)
    allows_custom_amount = db.Column(db.Boolean, default=True)
    minimum_amount = db.Column(db.Numeric(10, 2), default=0)
    maximum_amount = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Customization
    logo_url = db.Column(db.String(500), nullable=True)
    theme_color = db.Column(db.String(7), default='#36585C')
    success_message = db.Column(db.Text, nullable=True)
    thank_you_redirect = db.Column(db.String(500), nullable=True)
    
    # Fields collection
    collect_customer_name = db.Column(db.Boolean, default=True)
    collect_customer_email = db.Column(db.Boolean, default=True)
    collect_customer_phone = db.Column(db.Boolean, default=True)
    collect_payment_reason = db.Column(db.Boolean, default=False)
    custom_fields = db.Column(db.JSON, nullable=True)
    
    # Status and metrics
    is_active = db.Column(db.Boolean, default=True)
    total_payments = db.Column(db.Integer, default=0)
    total_amount_received = db.Column(db.Numeric(12, 2), default=0)
    page_views = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    company = db.relationship('Company', backref='payment_pages')
    creator = db.relationship('User', backref='created_payment_pages')
    
    def __repr__(self):
        return f"<PublicPaymentPage {self.page_name} (/{self.page_slug})>"


class PaymentPageTransaction(db.Model):
    __tablename__ = 'payment_page_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    payment_page_id = db.Column(db.Integer, db.ForeignKey('public_payment_pages.id'), nullable=False)
    
    # Customer details
    customer_name = db.Column(db.String(200), nullable=True)
    customer_email = db.Column(db.String(200), nullable=True)
    customer_phone = db.Column(db.String(20), nullable=True)
    payment_reason = db.Column(db.String(500), nullable=True)
    custom_data = db.Column(db.JSON, nullable=True)
    
    # Transaction details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='KES')
    payment_method = db.Column(db.String(20), nullable=False)  # mpesa, paypal, bank_transfer
    
    # Payment processing
    transaction_reference = db.Column(db.String(100), nullable=False, unique=True)
    external_reference = db.Column(db.String(100), nullable=True)  # M-Pesa code, PayPal ID, etc.
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed, cancelled
    
    # Metadata
    payment_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    payment_page = db.relationship('PublicPaymentPage', backref='transactions')
    
    def __repr__(self):
        return f"<PaymentPageTransaction {self.transaction_reference} - {self.amount} {self.currency}>"


class OnlineMeetingRoom(db.Model):
    __tablename__ = 'online_meeting_rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Room details
    room_name = db.Column(db.String(200), nullable=False)
    room_id = db.Column(db.String(100), nullable=False, unique=True)
    room_password = db.Column(db.String(50), nullable=True)
    
    # Room settings
    max_participants = db.Column(db.Integer, default=10)
    requires_password = db.Column(db.Boolean, default=False)
    waiting_room_enabled = db.Column(db.Boolean, default=True)
    recording_enabled = db.Column(db.Boolean, default=False)
    
    # Access control
    host_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    allowed_participants = db.Column(db.JSON, nullable=True)  # List of email addresses
    
    # Meeting URLs
    join_url = db.Column(db.String(500), nullable=False)
    start_url = db.Column(db.String(500), nullable=False)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    room_type = db.Column(db.String(20), default='permanent')  # permanent, scheduled
    
    # Usage stats
    total_meetings = db.Column(db.Integer, default=0)
    total_duration_minutes = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='meeting_rooms')
    host = db.relationship('User', backref='hosted_rooms')
    
    def __repr__(self):
        return f"<OnlineMeetingRoom {self.room_name} ({self.room_id})>"


class VoiceCommand(db.Model):
    __tablename__ = 'voice_commands'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Voice input
    audio_file_url = db.Column(db.String(500), nullable=True)
    transcribed_text = db.Column(db.Text, nullable=True)
    confidence_score = db.Column(db.Float, default=0.0)
    
    # Command analysis
    command_type = db.Column(db.String(50), nullable=True)  # create_invoice, add_task, record_sale, etc.
    intent = db.Column(db.String(100), nullable=True)
    entities = db.Column(db.JSON, nullable=True)  # Extracted entities like amounts, dates, names
    
    # Action taken
    action_performed = db.Column(db.String(100), nullable=True)
    created_record_id = db.Column(db.Integer, nullable=True)
    created_record_type = db.Column(db.String(50), nullable=True)
    
    # Processing status
    status = db.Column(db.String(20), default='processing')  # processing, completed, failed, ambiguous
    processing_time = db.Column(db.Float, default=0.0)  # in seconds
    error_message = db.Column(db.Text, nullable=True)
    
    # User feedback
    user_confirmed = db.Column(db.Boolean, nullable=True)
    user_feedback = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    company = db.relationship('Company', backref='voice_commands')
    user = db.relationship('User', backref='voice_commands')
    
    def __repr__(self):
        return f"<VoiceCommand {self.command_type} by {self.user_id} ({self.status})>"


class EmergencyFund(db.Model):
    __tablename__ = 'emergency_funds'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Fund configuration
    fund_name = db.Column(db.String(200), nullable=False)
    target_amount = db.Column(db.Numeric(12, 2), nullable=False)
    current_amount = db.Column(db.Numeric(12, 2), default=0)
    
    # Auto-contribution settings
    auto_contribution_enabled = db.Column(db.Boolean, default=False)
    contribution_percentage = db.Column(db.Float, default=0.0)  # % of monthly income
    contribution_frequency = db.Column(db.String(20), default='monthly')
    
    # Alert settings
    low_balance_threshold = db.Column(db.Numeric(10, 2), default=0)
    alert_when_used = db.Column(db.Boolean, default=True)
    alert_monthly_report = db.Column(db.Boolean, default=True)
    
    # Fund status
    is_active = db.Column(db.Boolean, default=True)
    last_contribution = db.Column(db.DateTime, nullable=True)
    last_withdrawal = db.Column(db.DateTime, nullable=True)
    
    # Progress tracking
    months_to_target = db.Column(db.Integer, nullable=True)
    target_completion_date = db.Column(db.Date, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    company = db.relationship('Company', backref='emergency_funds')
    creator = db.relationship('User', backref='created_emergency_funds')
    
    def __repr__(self):
        return f"<EmergencyFund {self.fund_name}: {self.current_amount}/{self.target_amount}>"
    
    @property
    def completion_percentage(self):
        """Calculate completion percentage"""
        if self.target_amount > 0:
            return min((float(self.current_amount) / float(self.target_amount)) * 100, 100)
        return 0


class EmergencyFundTransaction(db.Model):
    __tablename__ = 'emergency_fund_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    emergency_fund_id = db.Column(db.Integer, db.ForeignKey('emergency_funds.id'), nullable=False)
    
    # Transaction details
    transaction_type = db.Column(db.String(20), nullable=False)  # contribution, withdrawal
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    reason = db.Column(db.String(500), nullable=True)
    
    # Transaction metadata
    is_automatic = db.Column(db.Boolean, default=False)
    reference_number = db.Column(db.String(50), nullable=True)
    
    # Authorization (for withdrawals)
    authorized_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    requires_approval = db.Column(db.Boolean, default=False)
    approval_status = db.Column(db.String(20), default='approved')  # pending, approved, rejected
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    emergency_fund = db.relationship('EmergencyFund', backref='transactions')
    creator = db.relationship('User', foreign_keys=[created_by], backref='emergency_fund_transactions')
    authorizer = db.relationship('User', foreign_keys=[authorized_by], backref='authorized_emergency_transactions')
    
    def __repr__(self):
        return f"<EmergencyFundTransaction {self.transaction_type} {self.amount}>"


class WellnessTracker(db.Model):
    __tablename__ = 'wellness_tracker'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Daily mood and wellness
    date = db.Column(db.Date, nullable=False)
    mood_rating = db.Column(db.Integer, nullable=True)  # 1-5 scale
    stress_level = db.Column(db.Integer, nullable=True)  # 1-5 scale
    energy_level = db.Column(db.Integer, nullable=True)  # 1-5 scale
    
    # Work satisfaction
    job_satisfaction = db.Column(db.Integer, nullable=True)  # 1-5 scale
    work_life_balance = db.Column(db.Integer, nullable=True)  # 1-5 scale
    team_collaboration = db.Column(db.Integer, nullable=True)  # 1-5 scale
    
    # Feedback and comments
    feedback = db.Column(db.Text, nullable=True)
    concerns = db.Column(db.Text, nullable=True)
    suggestions = db.Column(db.Text, nullable=True)
    
    # Health indicators
    hours_slept = db.Column(db.Float, nullable=True)
    sick_day = db.Column(db.Boolean, default=False)
    taking_breaks = db.Column(db.Boolean, default=True)
    
    # Privacy settings
    is_anonymous = db.Column(db.Boolean, default=False)
    share_with_manager = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='wellness_records')
    employee = db.relationship('Employee', backref='wellness_data')
    user = db.relationship('User', backref='wellness_entries')
    
    def __repr__(self):
        return f"<WellnessTracker {self.date} - Employee {self.employee_id} (Mood: {self.mood_rating})>"


class CompanyBadge(db.Model):
    __tablename__ = 'company_badges'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Badge details
    badge_type = db.Column(db.String(50), nullable=False)  # trusted_seller, top_rated, verified, etc.
    badge_name = db.Column(db.String(100), nullable=False)
    badge_description = db.Column(db.Text, nullable=True)
    badge_icon = db.Column(db.String(200), nullable=True)
    badge_color = db.Column(db.String(7), default='#FFD700')
    
    # Achievement criteria
    criteria_met = db.Column(db.JSON, nullable=True)
    requirements = db.Column(db.JSON, nullable=True)
    
    # Badge status
    status = db.Column(db.String(20), default='active')  # active, suspended, revoked
    verification_status = db.Column(db.String(20), default='verified')  # verified, pending, rejected
    
    # Badge metrics
    score = db.Column(db.Float, default=0.0)
    rank = db.Column(db.Integer, nullable=True)
    
    # Visibility
    is_public = db.Column(db.Boolean, default=True)
    display_on_profile = db.Column(db.Boolean, default=True)
    
    # Dates
    earned_date = db.Column(db.Date, nullable=False)
    expires_date = db.Column(db.Date, nullable=True)
    last_verified = db.Column(db.Date, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    awarded_by = db.Column(db.String(100), default='System')
    
    # Relationships
    company = db.relationship('Company', backref='badges')
    
    def __repr__(self):
        return f"<CompanyBadge {self.badge_name} for company {self.company_id} ({self.status})>"
    
    @classmethod
    def check_and_award_badges(cls, company_id):
        """Check if company qualifies for any new badges"""
        # This would contain logic to check various criteria and award badges
        from models.company import Company
        from models.vendor_rating import VendorRating
        
        company = Company.query.get(company_id)
        if not company:
            return []
        
        new_badges = []
        
        # Example: Trusted Seller badge (based on ratings and transaction volume)
        avg_rating = db.session.query(func.avg(VendorRating.overall_rating)).filter(
            VendorRating.vendor_id == company_id
        ).scalar()
        
        if avg_rating and avg_rating >= 4.5:
            existing_badge = cls.query.filter_by(
                company_id=company_id,
                badge_type='trusted_seller'
            ).first()
            
            if not existing_badge:
                badge = cls(
                    company_id=company_id,
                    badge_type='trusted_seller',
                    badge_name='Trusted Seller',
                    badge_description='Consistently delivers high-quality products and services',
                    score=avg_rating,
                    earned_date=datetime.utcnow().date()
                )
                new_badges.append(badge)
        
        return new_badges


class AISmartAssistant(db.Model):
    __tablename__ = 'ai_smart_assistant'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Conversation details
    session_id = db.Column(db.String(100), nullable=False)
    message_type = db.Column(db.String(20), nullable=False)  # user_query, assistant_response
    message_content = db.Column(db.Text, nullable=False)
    
    # AI processing
    intent = db.Column(db.String(100), nullable=True)
    entities = db.Column(db.JSON, nullable=True)
    confidence_score = db.Column(db.Float, default=0.0)
    
    # Context and actions
    context_data = db.Column(db.JSON, nullable=True)
    suggested_actions = db.Column(db.JSON, nullable=True)
    actions_taken = db.Column(db.JSON, nullable=True)
    
    # Performance metrics
    response_time = db.Column(db.Float, default=0.0)  # in seconds
    user_rating = db.Column(db.Integer, nullable=True)  # 1-5 stars
    was_helpful = db.Column(db.Boolean, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='ai_assistant_logs')
    user = db.relationship('User', backref='ai_assistant_interactions')
    
    def __repr__(self):
        return f"<AISmartAssistant {self.message_type} in session {self.session_id}>"
