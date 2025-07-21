from models import db
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_

class Lead(db.Model):
    """Lead management for potential customers"""
    __tablename__ = 'leads'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    mobile = db.Column(db.String(50), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    
    # Address information
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    
    # Lead details
    lead_source = db.Column(db.String(100), nullable=True)  # Website, Referral, Cold Call, etc.
    lead_status = db.Column(db.String(50), default='new')  # new, contacted, qualified, converted, lost
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    industry = db.Column(db.String(100), nullable=True)
    job_title = db.Column(db.String(100), nullable=True)
    annual_revenue = db.Column(db.Float, nullable=True)
    number_of_employees = db.Column(db.Integer, nullable=True)
    
    # Lead scoring and qualification
    lead_score = db.Column(db.Integer, default=0)  # 0-100 scoring system
    qualification_status = db.Column(db.String(50), default='unqualified')  # unqualified, marketing_qualified, sales_qualified
    budget = db.Column(db.Float, nullable=True)
    timeline = db.Column(db.String(100), nullable=True)  # immediate, 1-3 months, 3-6 months, etc.
    decision_maker = db.Column(db.Boolean, default=False)
    
    # Assignment and tracking
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_user = db.relationship('User', foreign_keys=[assigned_to])
    
    # Conversion tracking
    converted_to_customer = db.Column(db.Boolean, default=False)
    converted_date = db.Column(db.DateTime, nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    
    # Follow-up and communication
    last_contacted = db.Column(db.DateTime, nullable=True)
    next_follow_up = db.Column(db.DateTime, nullable=True)
    contact_count = db.Column(db.Integer, default=0)
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(500), nullable=True)  # Comma-separated tags
    custom_fields = db.Column(db.JSON, nullable=True)  # For custom lead fields
    
    # Timestamps and company
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    activities = db.relationship('CRMActivity', backref='lead', lazy=True, cascade='all, delete-orphan')
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def days_since_created(self):
        return (datetime.utcnow() - self.created_at).days
    
    @property
    def days_since_contact(self):
        if self.last_contacted:
            return (datetime.utcnow() - self.last_contacted).days
        return None
    
    def get_lead_score_category(self):
        """Get lead score category"""
        if self.lead_score >= 80:
            return 'hot'
        elif self.lead_score >= 60:
            return 'warm'
        elif self.lead_score >= 40:
            return 'cold'
        else:
            return 'unscored'
    
    def update_lead_score(self):
        """Auto-calculate lead score based on various factors"""
        score = 0
        
        # Email engagement
        if self.email:
            score += 10
        
        # Phone provided
        if self.phone:
            score += 10
        
        # Company information
        if self.company_name:
            score += 15
        
        # Budget information
        if self.budget and self.budget > 0:
            score += 20
        
        # Decision maker
        if self.decision_maker:
            score += 25
        
        # Recent contact
        if self.last_contacted and self.days_since_contact <= 7:
            score += 10
        
        # Industry match (can be customized)
        if self.industry:
            score += 5
        
        # Timeline urgency
        if self.timeline in ['immediate', '1-3 months']:
            score += 15
        
        self.lead_score = min(score, 100)
        return self.lead_score
    
    @classmethod
    def get_lead_stats(cls, company_id):
        """Get lead statistics for dashboard"""
        total_leads = cls.query.filter_by(company_id=company_id).count()
        new_leads = cls.query.filter_by(company_id=company_id, lead_status='new').count()
        qualified_leads = cls.query.filter_by(company_id=company_id, qualification_status='sales_qualified').count()
        converted_leads = cls.query.filter_by(company_id=company_id, converted_to_customer=True).count()
        
        # Conversion rate
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        
        return {
            'total_leads': total_leads,
            'new_leads': new_leads,
            'qualified_leads': qualified_leads,
            'converted_leads': converted_leads,
            'conversion_rate': round(conversion_rate, 2)
        }
    
    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'company_name': self.company_name,
            'email': self.email,
            'phone': self.phone,
            'lead_status': self.lead_status,
            'lead_score': self.lead_score,
            'priority': self.priority,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else '',
            'last_contacted': self.last_contacted.strftime('%Y-%m-%d') if self.last_contacted else None
        }
    
    def __repr__(self):
        return f"<Lead {self.full_name} - {self.company_name}>"


class Customer(db.Model):
    """Customer management for converted leads and direct customers"""
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    customer_type = db.Column(db.String(50), default='individual')  # individual, business
    
    # Individual customer info
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    
    # Business customer info
    company_name = db.Column(db.String(200), nullable=True)
    business_type = db.Column(db.String(100), nullable=True)
    tax_id = db.Column(db.String(50), nullable=True)
    registration_number = db.Column(db.String(100), nullable=True)
    
    # Contact information
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    mobile = db.Column(db.String(50), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    
    # Address information
    billing_address = db.Column(db.Text, nullable=True)
    billing_city = db.Column(db.String(100), nullable=True)
    billing_state = db.Column(db.String(100), nullable=True)
    billing_country = db.Column(db.String(100), nullable=True)
    billing_postal_code = db.Column(db.String(20), nullable=True)
    
    shipping_address = db.Column(db.Text, nullable=True)
    shipping_city = db.Column(db.String(100), nullable=True)
    shipping_state = db.Column(db.String(100), nullable=True)
    shipping_country = db.Column(db.String(100), nullable=True)
    shipping_postal_code = db.Column(db.String(20), nullable=True)
    
    # Customer details
    customer_status = db.Column(db.String(50), default='active')  # active, inactive, blocked
    customer_segment = db.Column(db.String(100), nullable=True)  # VIP, Regular, New, etc.
    industry = db.Column(db.String(100), nullable=True)
    annual_revenue = db.Column(db.Float, nullable=True)
    number_of_employees = db.Column(db.Integer, nullable=True)
    
    # Financial information
    credit_limit = db.Column(db.Float, default=0.0)
    payment_terms = db.Column(db.String(50), default='net_30')  # net_15, net_30, net_60, cod
    preferred_payment_method = db.Column(db.String(50), nullable=True)
    
    # Sales tracking
    total_orders = db.Column(db.Integer, default=0)
    total_revenue = db.Column(db.Float, default=0.0)
    average_order_value = db.Column(db.Float, default=0.0)
    last_order_date = db.Column(db.DateTime, nullable=True)
    lifetime_value = db.Column(db.Float, default=0.0)
    
    # Assignment and management
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_user = db.relationship('User', foreign_keys=[assigned_to])
    
    # Communication preferences
    email_opt_in = db.Column(db.Boolean, default=True)
    sms_opt_in = db.Column(db.Boolean, default=False)
    marketing_opt_in = db.Column(db.Boolean, default=True)
    preferred_contact_method = db.Column(db.String(50), default='email')
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(500), nullable=True)
    custom_fields = db.Column(db.JSON, nullable=True)
    
    # Lead conversion tracking
    converted_from_lead = db.Column(db.Boolean, default=False)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    conversion_date = db.Column(db.DateTime, nullable=True)
    
    # Timestamps and company
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    activities = db.relationship('CRMActivity', backref='customer', lazy=True, cascade='all, delete-orphan')
    opportunities = db.relationship('Opportunity', backref='customer', lazy=True)
    sales = db.relationship('Sale', backref='customer', lazy=True)
    
    @property
    def display_name(self):
        if self.customer_type == 'business' and self.company_name:
            return self.company_name
        else:
            return f"{self.first_name or ''} {self.last_name or ''}".strip() or "Unknown Customer"
    
    @property
    def days_since_last_order(self):
        if self.last_order_date:
            return (datetime.utcnow() - self.last_order_date).days
        return None
    
    def update_sales_metrics(self):
        """Update customer sales metrics"""
        from models.sale import Sale
        
        sales = Sale.query.filter_by(customer_id=self.id, company_id=self.company_id).all()
        
        if sales:
            self.total_orders = len(sales)
            self.total_revenue = sum(sale.total_amount for sale in sales)
            self.average_order_value = self.total_revenue / self.total_orders
            self.last_order_date = max(sale.sale_date for sale in sales)
            self.lifetime_value = self.total_revenue  # Can be enhanced with future value prediction
        
        db.session.commit()
    
    def get_customer_value_segment(self):
        """Categorize customer based on lifetime value"""
        if self.lifetime_value >= 10000:
            return 'VIP'
        elif self.lifetime_value >= 5000:
            return 'Premium'
        elif self.lifetime_value >= 1000:
            return 'Standard'
        else:
            return 'Basic'
    
    @classmethod
    def get_customer_stats(cls, company_id):
        """Get customer statistics for dashboard"""
        total_customers = cls.query.filter_by(company_id=company_id).count()
        active_customers = cls.query.filter_by(company_id=company_id, customer_status='active').count()
        
        # Calculate total revenue
        customers = cls.query.filter_by(company_id=company_id).all()
        total_revenue = sum(c.total_revenue for c in customers)
        
        # Average customer value
        avg_customer_value = total_revenue / total_customers if total_customers > 0 else 0
        
        return {
            'total_customers': total_customers,
            'active_customers': active_customers,
            'total_revenue': total_revenue,
            'avg_customer_value': round(avg_customer_value, 2)
        }
    
    def to_dict(self):
        return {
            'id': self.id,
            'display_name': self.display_name,
            'customer_type': self.customer_type,
            'email': self.email,
            'phone': self.phone,
            'customer_status': self.customer_status,
            'total_revenue': self.total_revenue,
            'total_orders': self.total_orders,
            'created_at': self.created_at.strftime('%Y-%m-%d') if self.created_at else ''
        }
    
    def __repr__(self):
        return f"<Customer {self.display_name}>"


class Opportunity(db.Model):
    """Sales opportunity management"""
    __tablename__ = 'opportunities'

    id = db.Column(db.Integer, primary_key=True)
    opportunity_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Customer relationship
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    contact_person = db.Column(db.String(200), nullable=True)
    
    # Opportunity details
    opportunity_type = db.Column(db.String(100), nullable=True)  # New Business, Upsell, Renewal, etc.
    lead_source = db.Column(db.String(100), nullable=True)
    
    # Financial information
    estimated_value = db.Column(db.Float, nullable=False)
    actual_value = db.Column(db.Float, nullable=True)
    probability = db.Column(db.Integer, default=50)  # 0-100% chance of closing
    
    # Sales stage and timeline
    stage = db.Column(db.String(50), default='prospecting')  # prospecting, qualification, proposal, negotiation, closed_won, closed_lost
    expected_close_date = db.Column(db.Date, nullable=True)
    actual_close_date = db.Column(db.Date, nullable=True)
    
    # Status tracking
    status = db.Column(db.String(50), default='open')  # open, won, lost
    loss_reason = db.Column(db.String(200), nullable=True)
    competitor = db.Column(db.String(200), nullable=True)
    
    # Assignment and ownership
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_user = db.relationship('User', foreign_keys=[assigned_to])
    
    # Communication and follow-up
    last_activity_date = db.Column(db.DateTime, nullable=True)
    next_action = db.Column(db.String(200), nullable=True)
    next_action_date = db.Column(db.DateTime, nullable=True)
    
    # Additional information
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    tags = db.Column(db.String(500), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    custom_fields = db.Column(db.JSON, nullable=True)
    
    # Timestamps and company
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    activities = db.relationship('CRMActivity', backref='opportunity', lazy=True, cascade='all, delete-orphan')
    
    @property
    def weighted_value(self):
        """Calculate weighted value based on probability"""
        return self.estimated_value * (self.probability / 100)
    
    @property
    def days_to_close(self):
        """Days until expected close date"""
        if self.expected_close_date:
            return (self.expected_close_date - datetime.utcnow().date()).days
        return None
    
    @property
    def is_overdue(self):
        """Check if opportunity is past expected close date"""
        if self.expected_close_date and self.status == 'open':
            return datetime.utcnow().date() > self.expected_close_date
        return False
    
    def get_stage_progress(self):
        """Get numerical progress based on stage"""
        stage_progress = {
            'prospecting': 20,
            'qualification': 40,
            'proposal': 60,
            'negotiation': 80,
            'closed_won': 100,
            'closed_lost': 0
        }
        return stage_progress.get(self.stage, 0)
    
    @classmethod
    def get_pipeline_stats(cls, company_id):
        """Get sales pipeline statistics"""
        opportunities = cls.query.filter_by(company_id=company_id).all()
        
        total_opportunities = len(opportunities)
        open_opportunities = len([o for o in opportunities if o.status == 'open'])
        won_opportunities = len([o for o in opportunities if o.status == 'won'])
        
        total_pipeline_value = sum(o.estimated_value for o in opportunities if o.status == 'open')
        weighted_pipeline_value = sum(o.weighted_value for o in opportunities if o.status == 'open')
        
        # Win rate
        closed_opportunities = len([o for o in opportunities if o.status in ['won', 'lost']])
        win_rate = (won_opportunities / closed_opportunities * 100) if closed_opportunities > 0 else 0
        
        return {
            'total_opportunities': total_opportunities,
            'open_opportunities': open_opportunities,
            'won_opportunities': won_opportunities,
            'total_pipeline_value': total_pipeline_value,
            'weighted_pipeline_value': weighted_pipeline_value,
            'win_rate': round(win_rate, 2)
        }
    
    def to_dict(self):
        return {
            'id': self.id,
            'opportunity_name': self.opportunity_name,
            'customer_name': self.customer.display_name if self.customer else '',
            'estimated_value': self.estimated_value,
            'probability': self.probability,
            'stage': self.stage,
            'status': self.status,
            'expected_close_date': self.expected_close_date.strftime('%Y-%m-%d') if self.expected_close_date else '',
            'created_at': self.created_at.strftime('%Y-%m-%d') if self.created_at else ''
        }
    
    def __repr__(self):
        return f"<Opportunity {self.opportunity_name} - {self.estimated_value}>"


class CRMActivity(db.Model):
    """Track all CRM activities (calls, emails, meetings, etc.)"""
    __tablename__ = 'crm_activities'

    id = db.Column(db.Integer, primary_key=True)
    activity_type = db.Column(db.String(50), nullable=False)  # call, email, meeting, task, note
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Activity details
    activity_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    duration = db.Column(db.Integer, nullable=True)  # Duration in minutes
    status = db.Column(db.String(50), default='pending')  # pending, completed, cancelled
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    
    # Relationships (activity can be related to lead, customer, or opportunity)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id'), nullable=True)
    
    # Assignment
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_user = db.relationship('User', foreign_keys=[assigned_to])
    
    # Communication details
    outcome = db.Column(db.String(200), nullable=True)
    follow_up_required = db.Column(db.Boolean, default=False)
    follow_up_date = db.Column(db.DateTime, nullable=True)
    
    # Additional information
    location = db.Column(db.String(200), nullable=True)
    participants = db.Column(db.Text, nullable=True)  # JSON string of participants
    attachments = db.Column(db.Text, nullable=True)  # JSON string of attachment URLs
    tags = db.Column(db.String(500), nullable=True)
    
    # Timestamps and company
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    @property
    def related_entity(self):
        """Get the main entity this activity relates to"""
        if self.lead_id and self.lead:
            return f"Lead: {self.lead.full_name}"
        elif self.customer_id and self.customer:
            return f"Customer: {self.customer.display_name}"
        elif self.opportunity_id and self.opportunity:
            return f"Opportunity: {self.opportunity.opportunity_name}"
        return "Unknown"
    
    @property
    def is_overdue(self):
        """Check if activity is overdue"""
        if self.due_date and self.status == 'pending':
            return datetime.utcnow() > self.due_date
        return False
    
    @classmethod
    def get_activity_stats(cls, company_id, user_id=None):
        """Get activity statistics"""
        query = cls.query.filter_by(company_id=company_id)
        if user_id:
            query = query.filter_by(assigned_to=user_id)
        
        activities = query.all()
        
        total_activities = len(activities)
        pending_activities = len([a for a in activities if a.status == 'pending'])
        completed_activities = len([a for a in activities if a.status == 'completed'])
        overdue_activities = len([a for a in activities if a.is_overdue])
        
        return {
            'total_activities': total_activities,
            'pending_activities': pending_activities,
            'completed_activities': completed_activities,
            'overdue_activities': overdue_activities
        }
    
    def to_dict(self):
        return {
            'id': self.id,
            'activity_type': self.activity_type,
            'subject': self.subject,
            'description': self.description,
            'activity_date': self.activity_date.strftime('%Y-%m-%d %H:%M') if self.activity_date else '',
            'due_date': self.due_date.strftime('%Y-%m-%d %H:%M') if self.due_date else '',
            'status': self.status,
            'priority': self.priority,
            'related_entity': self.related_entity
        }
    
    def __repr__(self):
        return f"<CRMActivity {self.activity_type} - {self.subject}>"


class CRMTask(db.Model):
    """CRM tasks and reminders"""
    __tablename__ = 'crm_tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    task_type = db.Column(db.String(50), default='general')  # follow_up, proposal, demo, etc.
    
    # Task scheduling
    due_date = db.Column(db.DateTime, nullable=True)
    reminder_date = db.Column(db.DateTime, nullable=True)
    completed_date = db.Column(db.DateTime, nullable=True)
    
    # Status and priority
    status = db.Column(db.String(50), default='pending')  # pending, in_progress, completed, cancelled
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    
    # Relationships
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id'), nullable=True)
    
    lead = db.relationship('Lead', backref='tasks')
    customer = db.relationship('Customer', backref='tasks')
    opportunity = db.relationship('Opportunity', backref='tasks')
    
    # Assignment
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_user = db.relationship('User', foreign_keys=[assigned_to])
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(500), nullable=True)
    
    # Timestamps and company
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    @property
    def is_overdue(self):
        """Check if task is overdue"""
        if self.due_date and self.status in ['pending', 'in_progress']:
            return datetime.utcnow() > self.due_date
        return False
    
    @property
    def related_entity_name(self):
        """Get name of related entity"""
        if self.lead:
            return self.lead.full_name
        elif self.customer:
            return self.customer.display_name
        elif self.opportunity:
            return self.opportunity.opportunity_name
        return "No relation"
    
    def __repr__(self):
        return f"<CRMTask {self.title}>"


class CRMNote(db.Model):
    """Notes attached to CRM entities"""
    __tablename__ = 'crm_notes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=False)
    note_type = db.Column(db.String(50), default='general')  # general, meeting, call, etc.
    
    # Relationships
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id'), nullable=True)
    
    lead = db.relationship('Lead', backref='notes')
    customer = db.relationship('Customer', backref='notes')
    opportunity = db.relationship('Opportunity', backref='notes')
    
    # Privacy and sharing
    is_private = db.Column(db.Boolean, default=False)
    shared_with = db.Column(db.Text, nullable=True)  # JSON list of user IDs
    
    # Timestamps and company
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    def __repr__(self):
        return f"<CRMNote {self.title or 'Untitled'}>"
