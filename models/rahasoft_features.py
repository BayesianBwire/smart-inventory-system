from datetime import datetime, timedelta
from extensions import db
from sqlalchemy import func
import json

class OfflineDataSync(db.Model):
    __tablename__ = 'offline_data_sync'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Sync details
    device_id = db.Column(db.String(100), nullable=False)
    data_type = db.Column(db.String(50), nullable=False)  # inventory, sales, customers, etc.
    offline_data = db.Column(db.JSON, nullable=False)
    
    # Sync status
    sync_status = db.Column(db.String(20), default='pending')  # pending, synced, conflict, failed
    last_sync_attempt = db.Column(db.DateTime, nullable=True)
    sync_conflicts = db.Column(db.JSON, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    synced_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    company = db.relationship('Company', backref='offline_syncs')
    user = db.relationship('User', backref='offline_data')
    
    def __repr__(self):
        return f"<OfflineDataSync {self.data_type} - {self.sync_status}>"


class SmartReceiptScanner(db.Model):
    __tablename__ = 'smart_receipt_scanner'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Receipt details
    receipt_image_url = db.Column(db.String(500), nullable=False)
    extracted_text = db.Column(db.Text, nullable=True)
    merchant_name = db.Column(db.String(200), nullable=True)
    transaction_amount = db.Column(db.Numeric(10, 2), nullable=True)
    transaction_date = db.Column(db.DateTime, nullable=True)
    
    # M-Pesa matching
    mpesa_code = db.Column(db.String(20), nullable=True)
    is_mpesa_matched = db.Column(db.Boolean, default=False)
    confidence_score = db.Column(db.Float, default=0.0)
    
    # Bill matching
    matched_bill_id = db.Column(db.Integer, nullable=True)
    is_bill_matched = db.Column(db.Boolean, default=False)
    
    # Processing status
    processing_status = db.Column(db.String(20), default='processing')  # processing, completed, failed
    extracted_data = db.Column(db.JSON, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    company = db.relationship('Company', backref='scanned_receipts')
    user = db.relationship('User', backref='receipt_scans')
    
    def __repr__(self):
        return f"<SmartReceiptScanner {self.merchant_name} - {self.transaction_amount}>"


class BusinessCalendar(db.Model):
    __tablename__ = 'business_calendar'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Event details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    event_type = db.Column(db.String(50), nullable=False)  # holiday, meeting, deadline, etc.
    
    # Date and time
    event_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    is_all_day = db.Column(db.Boolean, default=False)
    
    # Kenyan-specific
    is_kenyan_holiday = db.Column(db.Boolean, default=False)
    holiday_category = db.Column(db.String(50), nullable=True)  # national, religious, cultural
    
    # Notifications
    reminder_enabled = db.Column(db.Boolean, default=True)
    reminder_minutes = db.Column(db.Integer, default=60)
    
    # Recurrence
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_pattern = db.Column(db.String(50), nullable=True)  # daily, weekly, monthly, yearly
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    company = db.relationship('Company', backref='calendar_events')
    creator = db.relationship('User', backref='created_events')
    
    def __repr__(self):
        return f"<BusinessCalendar {self.title} - {self.event_date}>"
    
    @classmethod
    def get_kenyan_holidays(cls, year=None):
        """Get Kenyan holidays for the year"""
        if year is None:
            year = datetime.utcnow().year
        
        # Define Kenyan holidays
        holidays = [
            {'title': 'New Year\'s Day', 'date': f'{year}-01-01', 'category': 'national'},
            {'title': 'Labour Day', 'date': f'{year}-05-01', 'category': 'national'},
            {'title': 'Madaraka Day', 'date': f'{year}-06-01', 'category': 'national'},
            {'title': 'Mashujaa Day', 'date': f'{year}-10-20', 'category': 'national'},
            {'title': 'Jamhuri Day', 'date': f'{year}-12-12', 'category': 'national'},
            {'title': 'Christmas Day', 'date': f'{year}-12-25', 'category': 'religious'},
            {'title': 'Boxing Day', 'date': f'{year}-12-26', 'category': 'national'},
        ]
        
        return holidays


class VendorRating(db.Model):
    __tablename__ = 'vendor_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable=False)
    rated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Rating details
    overall_rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    delivery_rating = db.Column(db.Integer, nullable=True)
    quality_rating = db.Column(db.Integer, nullable=True)
    communication_rating = db.Column(db.Integer, nullable=True)
    pricing_rating = db.Column(db.Integer, nullable=True)
    
    # Review
    review_title = db.Column(db.String(200), nullable=True)
    review_text = db.Column(db.Text, nullable=True)
    
    # Transaction reference
    order_reference = db.Column(db.String(100), nullable=True)
    transaction_amount = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Status
    is_verified = db.Column(db.Boolean, default=False)
    is_anonymous = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='vendor_ratings')
    vendor = db.relationship('Contact', backref='received_ratings')
    rater = db.relationship('User', backref='given_ratings')
    
    def __repr__(self):
        return f"<VendorRating {self.overall_rating} stars for vendor {self.vendor_id}>"


class SMSWhatsAppNotification(db.Model):
    __tablename__ = 'sms_whatsapp_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Recipient details
    recipient_phone = db.Column(db.String(20), nullable=False)
    recipient_name = db.Column(db.String(200), nullable=True)
    
    # Message details
    message_type = db.Column(db.String(50), nullable=False)  # sms, whatsapp
    notification_type = db.Column(db.String(50), nullable=False)  # reminder, payment, alert
    subject = db.Column(db.String(200), nullable=True)
    message_content = db.Column(db.Text, nullable=False)
    
    # Delivery status
    status = db.Column(db.String(20), default='pending')  # pending, sent, delivered, failed
    sent_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    
    # Provider details
    provider = db.Column(db.String(50), nullable=True)  # africastalking, twilio, etc.
    provider_message_id = db.Column(db.String(100), nullable=True)
    cost = db.Column(db.Numeric(6, 4), nullable=True)
    
    # Scheduling
    scheduled_for = db.Column(db.DateTime, nullable=True)
    is_scheduled = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    company = db.relationship('Company', backref='notifications_sent')
    sender = db.relationship('User', backref='sent_notifications')
    
    def __repr__(self):
        return f"<SMSWhatsAppNotification {self.message_type} to {self.recipient_phone}>"


class BusinessHealthScore(db.Model):
    __tablename__ = 'business_health_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Score components
    financial_health = db.Column(db.Float, default=0.0)  # 0-100
    operational_efficiency = db.Column(db.Float, default=0.0)
    customer_satisfaction = db.Column(db.Float, default=0.0)
    inventory_management = db.Column(db.Float, default=0.0)
    cash_flow_health = db.Column(db.Float, default=0.0)
    
    # Overall score
    overall_score = db.Column(db.Float, default=0.0)
    score_grade = db.Column(db.String(2), default='F')  # A+, A, B+, B, C+, C, D, F
    
    # Insights and recommendations
    key_insights = db.Column(db.JSON, nullable=True)
    recommendations = db.Column(db.JSON, nullable=True)
    red_flags = db.Column(db.JSON, nullable=True)
    
    # Calculation period
    calculation_date = db.Column(db.Date, nullable=False)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='health_scores')
    
    def __repr__(self):
        return f"<BusinessHealthScore {self.overall_score}% ({self.score_grade}) for company {self.company_id}>"
    
    @classmethod
    def calculate_health_score(cls, company_id):
        """Calculate business health score for a company"""
        # This would contain complex business logic to calculate various metrics
        # For now, returning a placeholder
        return {
            'financial_health': 85.0,
            'operational_efficiency': 78.0,
            'customer_satisfaction': 92.0,
            'inventory_management': 73.0,
            'cash_flow_health': 68.0,
            'overall_score': 79.2,
            'score_grade': 'B+'
        }


class LocalizedTraining(db.Model):
    __tablename__ = 'localized_training'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Training content
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    content_type = db.Column(db.String(50), nullable=False)  # video, article, quiz, interactive
    content_url = db.Column(db.String(500), nullable=True)
    content_text = db.Column(db.Text, nullable=True)
    
    # Localization
    language = db.Column(db.String(10), default='en')  # en, sw (Swahili)
    country_focus = db.Column(db.String(10), default='KE')  # KE (Kenya)
    
    # Categorization
    category = db.Column(db.String(50), nullable=False)  # finance, inventory, sales, hr
    difficulty_level = db.Column(db.String(20), default='beginner')  # beginner, intermediate, advanced
    estimated_duration = db.Column(db.Integer, default=0)  # in minutes
    
    # Content metadata
    tags = db.Column(db.JSON, nullable=True)
    prerequisites = db.Column(db.JSON, nullable=True)
    learning_objectives = db.Column(db.JSON, nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    creator = db.relationship('User', backref='created_training')
    
    def __repr__(self):
        return f"<LocalizedTraining {self.title} ({self.language})>"


class TrainingProgress(db.Model):
    __tablename__ = 'training_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    training_id = db.Column(db.Integer, db.ForeignKey('localized_training.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Progress tracking
    status = db.Column(db.String(20), default='not_started')  # not_started, in_progress, completed
    progress_percentage = db.Column(db.Float, default=0.0)
    time_spent = db.Column(db.Integer, default=0)  # in minutes
    
    # Assessment
    quiz_score = db.Column(db.Float, nullable=True)
    quiz_attempts = db.Column(db.Integer, default=0)
    passed = db.Column(db.Boolean, default=False)
    
    # Feedback
    user_rating = db.Column(db.Integer, nullable=True)  # 1-5 stars
    user_feedback = db.Column(db.Text, nullable=True)
    
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='training_progress')
    training = db.relationship('LocalizedTraining', backref='user_progress')
    company = db.relationship('Company', backref='training_records')
    
    def __repr__(self):
        return f"<TrainingProgress {self.user_id} - {self.training_id} ({self.progress_percentage}%)>"


class CommunityGroup(db.Model):
    __tablename__ = 'community_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Group details
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    industry = db.Column(db.String(100), nullable=False)  # retail, wholesale, manufacturing, etc.
    group_type = db.Column(db.String(50), default='industry')  # industry, location, size
    
    # Group settings
    is_public = db.Column(db.Boolean, default=True)
    requires_approval = db.Column(db.Boolean, default=False)
    max_members = db.Column(db.Integer, nullable=True)
    
    # Location-based
    country = db.Column(db.String(50), default='Kenya')
    city = db.Column(db.String(100), nullable=True)
    
    # Group stats
    member_count = db.Column(db.Integer, default=0)
    post_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    creator = db.relationship('User', backref='created_groups')
    
    def __repr__(self):
        return f"<CommunityGroup {self.name} ({self.industry})>"


class CommunityMembership(db.Model):
    __tablename__ = 'community_memberships'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('community_groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Membership details
    role = db.Column(db.String(20), default='member')  # member, moderator, admin
    status = db.Column(db.String(20), default='active')  # pending, active, suspended, banned
    
    # Engagement metrics
    posts_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    likes_given = db.Column(db.Integer, default=0)
    likes_received = db.Column(db.Integer, default=0)
    
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    group = db.relationship('CommunityGroup', backref='memberships')
    user = db.relationship('User', backref='group_memberships')
    company = db.relationship('Company', backref='community_memberships')
    
    def __repr__(self):
        return f"<CommunityMembership {self.user_id} in {self.group_id} ({self.role})>"


class CommunityPost(db.Model):
    __tablename__ = 'community_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('community_groups.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Post content
    title = db.Column(db.String(300), nullable=False)
    content = db.Column(db.Text, nullable=False)
    post_type = db.Column(db.String(50), default='discussion')  # discussion, question, announcement, poll
    
    # Media attachments
    image_urls = db.Column(db.JSON, nullable=True)
    video_url = db.Column(db.String(500), nullable=True)
    document_urls = db.Column(db.JSON, nullable=True)
    
    # Engagement metrics
    likes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    shares_count = db.Column(db.Integer, default=0)
    views_count = db.Column(db.Integer, default=0)
    
    # Moderation
    is_pinned = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    is_moderated = db.Column(db.Boolean, default=False)
    moderation_reason = db.Column(db.String(200), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    group = db.relationship('CommunityGroup', backref='posts')
    author = db.relationship('User', backref='community_posts')
    company = db.relationship('Company', backref='community_posts')
    
    def __repr__(self):
        return f"<CommunityPost '{self.title}' by {self.author_id}>"
