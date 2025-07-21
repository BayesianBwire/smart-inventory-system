from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FloatField, IntegerField, BooleanField, DateField, DateTimeField
from wtforms.validators import DataRequired, Email, Optional, NumberRange, Length, ValidationError
from models.crm import Lead, Customer, Opportunity
from flask_login import current_user

class LeadForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=1, max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=1, max=100)])
    company_name = StringField('Company Name', validators=[Optional(), Length(max=200)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField('Phone', validators=[Optional(), Length(max=50)])
    mobile = StringField('Mobile', validators=[Optional(), Length(max=50)])
    website = StringField('Website', validators=[Optional(), Length(max=255)])
    
    # Address
    address = TextAreaField('Address', validators=[Optional()])
    city = StringField('City', validators=[Optional(), Length(max=100)])
    state = StringField('State', validators=[Optional(), Length(max=100)])
    country = StringField('Country', validators=[Optional(), Length(max=100)])
    postal_code = StringField('Postal Code', validators=[Optional(), Length(max=20)])
    
    # Lead details
    lead_source = SelectField('Lead Source', 
                             choices=[('', 'Select Source'), ('website', 'Website'), ('referral', 'Referral'), 
                                     ('cold_call', 'Cold Call'), ('email_campaign', 'Email Campaign'), 
                                     ('social_media', 'Social Media'), ('trade_show', 'Trade Show'), 
                                     ('advertisement', 'Advertisement'), ('other', 'Other')],
                             validators=[Optional()])
    
    lead_status = SelectField('Lead Status',
                             choices=[('new', 'New'), ('contacted', 'Contacted'), ('qualified', 'Qualified'), 
                                     ('converted', 'Converted'), ('lost', 'Lost')],
                             default='new', validators=[DataRequired()])
    
    priority = SelectField('Priority',
                          choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
                          default='medium', validators=[DataRequired()])
    
    industry = StringField('Industry', validators=[Optional(), Length(max=100)])
    job_title = StringField('Job Title', validators=[Optional(), Length(max=100)])
    annual_revenue = FloatField('Annual Revenue', validators=[Optional(), NumberRange(min=0)])
    number_of_employees = IntegerField('Number of Employees', validators=[Optional(), NumberRange(min=1)])
    
    # Qualification
    qualification_status = SelectField('Qualification Status',
                                      choices=[('unqualified', 'Unqualified'), 
                                              ('marketing_qualified', 'Marketing Qualified'),
                                              ('sales_qualified', 'Sales Qualified')],
                                      default='unqualified')
    
    budget = FloatField('Budget', validators=[Optional(), NumberRange(min=0)])
    timeline = SelectField('Timeline',
                          choices=[('', 'Select Timeline'), ('immediate', 'Immediate'), 
                                  ('1-3 months', '1-3 Months'), ('3-6 months', '3-6 Months'),
                                  ('6-12 months', '6-12 Months'), ('12+ months', '12+ Months')],
                          validators=[Optional()])
    
    decision_maker = BooleanField('Is Decision Maker')
    
    # Follow-up
    next_follow_up = DateTimeField('Next Follow-up', validators=[Optional()], format='%Y-%m-%d %H:%M')
    
    # Additional
    notes = TextAreaField('Notes', validators=[Optional()])
    tags = StringField('Tags (comma separated)', validators=[Optional(), Length(max=500)])
    
    def validate_email(self, field):
        if current_user.is_authenticated:
            existing_lead = Lead.query.filter_by(
                email=field.data,
                company_id=current_user.company_id
            ).first()
            if existing_lead and (not hasattr(self, 'lead_id') or existing_lead.id != self.lead_id):
                raise ValidationError('A lead with this email already exists.')


class CustomerForm(FlaskForm):
    customer_type = SelectField('Customer Type',
                               choices=[('individual', 'Individual'), ('business', 'Business')],
                               default='individual', validators=[DataRequired()])
    
    # Individual info
    first_name = StringField('First Name', validators=[Optional(), Length(max=100)])
    last_name = StringField('Last Name', validators=[Optional(), Length(max=100)])
    
    # Business info
    company_name = StringField('Company Name', validators=[Optional(), Length(max=200)])
    business_type = StringField('Business Type', validators=[Optional(), Length(max=100)])
    tax_id = StringField('Tax ID', validators=[Optional(), Length(max=50)])
    registration_number = StringField('Registration Number', validators=[Optional(), Length(max=100)])
    
    # Contact info
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField('Phone', validators=[Optional(), Length(max=50)])
    mobile = StringField('Mobile', validators=[Optional(), Length(max=50)])
    website = StringField('Website', validators=[Optional(), Length(max=255)])
    
    # Billing address
    billing_address = TextAreaField('Billing Address', validators=[Optional()])
    billing_city = StringField('Billing City', validators=[Optional(), Length(max=100)])
    billing_state = StringField('Billing State', validators=[Optional(), Length(max=100)])
    billing_country = StringField('Billing Country', validators=[Optional(), Length(max=100)])
    billing_postal_code = StringField('Billing Postal Code', validators=[Optional(), Length(max=20)])
    
    # Shipping address
    shipping_address = TextAreaField('Shipping Address', validators=[Optional()])
    shipping_city = StringField('Shipping City', validators=[Optional(), Length(max=100)])
    shipping_state = StringField('Shipping State', validators=[Optional(), Length(max=100)])
    shipping_country = StringField('Shipping Country', validators=[Optional(), Length(max=100)])
    shipping_postal_code = StringField('Shipping Postal Code', validators=[Optional(), Length(max=20)])
    
    # Customer details
    customer_status = SelectField('Customer Status',
                                 choices=[('active', 'Active'), ('inactive', 'Inactive'), ('blocked', 'Blocked')],
                                 default='active', validators=[DataRequired()])
    
    customer_segment = SelectField('Customer Segment',
                                  choices=[('', 'Select Segment'), ('vip', 'VIP'), ('premium', 'Premium'),
                                          ('standard', 'Standard'), ('basic', 'Basic')],
                                  validators=[Optional()])
    
    industry = StringField('Industry', validators=[Optional(), Length(max=100)])
    annual_revenue = FloatField('Annual Revenue', validators=[Optional(), NumberRange(min=0)])
    number_of_employees = IntegerField('Number of Employees', validators=[Optional(), NumberRange(min=1)])
    
    # Financial
    credit_limit = FloatField('Credit Limit', validators=[Optional(), NumberRange(min=0)], default=0)
    payment_terms = SelectField('Payment Terms',
                               choices=[('net_15', 'Net 15'), ('net_30', 'Net 30'), ('net_60', 'Net 60'), ('cod', 'COD')],
                               default='net_30', validators=[DataRequired()])
    
    preferred_payment_method = SelectField('Preferred Payment Method',
                                          choices=[('', 'Select Method'), ('cash', 'Cash'), ('check', 'Check'),
                                                  ('credit_card', 'Credit Card'), ('bank_transfer', 'Bank Transfer'),
                                                  ('mobile_money', 'Mobile Money')],
                                          validators=[Optional()])
    
    # Communication preferences
    email_opt_in = BooleanField('Email Opt-in', default=True)
    sms_opt_in = BooleanField('SMS Opt-in', default=False)
    marketing_opt_in = BooleanField('Marketing Opt-in', default=True)
    preferred_contact_method = SelectField('Preferred Contact Method',
                                          choices=[('email', 'Email'), ('phone', 'Phone'), ('sms', 'SMS')],
                                          default='email')
    
    # Additional
    notes = TextAreaField('Notes', validators=[Optional()])
    tags = StringField('Tags (comma separated)', validators=[Optional(), Length(max=500)])
    
    def validate_email(self, field):
        if current_user.is_authenticated:
            existing_customer = Customer.query.filter_by(
                email=field.data,
                company_id=current_user.company_id
            ).first()
            if existing_customer and (not hasattr(self, 'customer_id') or existing_customer.id != self.customer_id):
                raise ValidationError('A customer with this email already exists.')


class OpportunityForm(FlaskForm):
    opportunity_name = StringField('Opportunity Name', validators=[DataRequired(), Length(min=1, max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    
    # Customer selection (will be populated dynamically)
    customer_id = SelectField('Customer', choices=[], validators=[DataRequired()], coerce=int)
    contact_person = StringField('Contact Person', validators=[Optional(), Length(max=200)])
    
    # Opportunity details
    opportunity_type = SelectField('Opportunity Type',
                                  choices=[('', 'Select Type'), ('new_business', 'New Business'),
                                          ('upsell', 'Upsell'), ('cross_sell', 'Cross-sell'),
                                          ('renewal', 'Renewal'), ('expansion', 'Expansion')],
                                  validators=[Optional()])
    
    lead_source = SelectField('Lead Source',
                             choices=[('', 'Select Source'), ('website', 'Website'), ('referral', 'Referral'),
                                     ('cold_call', 'Cold Call'), ('email_campaign', 'Email Campaign'),
                                     ('social_media', 'Social Media'), ('trade_show', 'Trade Show'),
                                     ('advertisement', 'Advertisement'), ('existing_customer', 'Existing Customer')],
                             validators=[Optional()])
    
    # Financial
    estimated_value = FloatField('Estimated Value', validators=[DataRequired(), NumberRange(min=0)])
    probability = IntegerField('Probability (%)', validators=[DataRequired(), NumberRange(min=0, max=100)], default=50)
    
    # Sales stage
    stage = SelectField('Stage',
                       choices=[('prospecting', 'Prospecting'), ('qualification', 'Qualification'),
                               ('proposal', 'Proposal'), ('negotiation', 'Negotiation'),
                               ('closed_won', 'Closed Won'), ('closed_lost', 'Closed Lost')],
                       default='prospecting', validators=[DataRequired()])
    
    # Timeline
    expected_close_date = DateField('Expected Close Date', validators=[Optional()])
    
    # Status and management
    priority = SelectField('Priority',
                          choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
                          default='medium', validators=[DataRequired()])
    
    # Follow-up
    next_action = StringField('Next Action', validators=[Optional(), Length(max=200)])
    next_action_date = DateTimeField('Next Action Date', validators=[Optional()], format='%Y-%m-%d %H:%M')
    
    # Additional
    notes = TextAreaField('Notes', validators=[Optional()])
    tags = StringField('Tags (comma separated)', validators=[Optional(), Length(max=500)])
    
    def __init__(self, *args, **kwargs):
        super(OpportunityForm, self).__init__(*args, **kwargs)
        if current_user.is_authenticated:
            # Populate customer choices
            customers = Customer.query.filter_by(
                company_id=current_user.company_id,
                customer_status='active'
            ).order_by(Customer.company_name, Customer.first_name).all()
            
            self.customer_id.choices = [(c.id, c.display_name) for c in customers]


class CRMActivityForm(FlaskForm):
    activity_type = SelectField('Activity Type',
                               choices=[('call', 'Phone Call'), ('email', 'Email'), ('meeting', 'Meeting'),
                                       ('task', 'Task'), ('note', 'Note'), ('demo', 'Demo'),
                                       ('proposal', 'Proposal'), ('follow_up', 'Follow-up')],
                               validators=[DataRequired()])
    
    subject = StringField('Subject', validators=[DataRequired(), Length(min=1, max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    
    # Scheduling
    activity_date = DateTimeField('Activity Date', validators=[DataRequired()], format='%Y-%m-%d %H:%M')
    due_date = DateTimeField('Due Date', validators=[Optional()], format='%Y-%m-%d %H:%M')
    duration = IntegerField('Duration (minutes)', validators=[Optional(), NumberRange(min=1)])
    
    # Status and priority
    status = SelectField('Status',
                        choices=[('pending', 'Pending'), ('completed', 'Completed'), ('cancelled', 'Cancelled')],
                        default='pending', validators=[DataRequired()])
    
    priority = SelectField('Priority',
                          choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
                          default='medium', validators=[DataRequired()])
    
    # Relationships
    lead_id = SelectField('Related Lead', choices=[('', 'No Lead')], validators=[Optional()], coerce=int)
    customer_id = SelectField('Related Customer', choices=[('', 'No Customer')], validators=[Optional()], coerce=int)
    opportunity_id = SelectField('Related Opportunity', choices=[('', 'No Opportunity')], validators=[Optional()], coerce=int)
    
    # Communication details
    outcome = StringField('Outcome', validators=[Optional(), Length(max=200)])
    follow_up_required = BooleanField('Follow-up Required')
    follow_up_date = DateTimeField('Follow-up Date', validators=[Optional()], format='%Y-%m-%d %H:%M')
    
    # Additional
    location = StringField('Location', validators=[Optional(), Length(max=200)])
    participants = TextAreaField('Participants', validators=[Optional()])
    tags = StringField('Tags (comma separated)', validators=[Optional(), Length(max=500)])
    
    def __init__(self, *args, **kwargs):
        super(CRMActivityForm, self).__init__(*args, **kwargs)
        if current_user.is_authenticated:
            # Populate relationship choices
            leads = Lead.query.filter_by(
                company_id=current_user.company_id,
                lead_status__ne='converted'
            ).order_by(Lead.first_name, Lead.last_name).all()
            self.lead_id.choices = [('', 'No Lead')] + [(l.id, l.full_name) for l in leads]
            
            customers = Customer.query.filter_by(
                company_id=current_user.company_id,
                customer_status='active'
            ).order_by(Customer.company_name, Customer.first_name).all()
            self.customer_id.choices = [('', 'No Customer')] + [(c.id, c.display_name) for c in customers]
            
            opportunities = Opportunity.query.filter_by(
                company_id=current_user.company_id,
                status='open'
            ).order_by(Opportunity.opportunity_name).all()
            self.opportunity_id.choices = [('', 'No Opportunity')] + [(o.id, o.opportunity_name) for o in opportunities]


class CRMTaskForm(FlaskForm):
    title = StringField('Task Title', validators=[DataRequired(), Length(min=1, max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    task_type = SelectField('Task Type',
                           choices=[('general', 'General'), ('follow_up', 'Follow-up'), 
                                   ('proposal', 'Proposal'), ('demo', 'Demo'),
                                   ('meeting', 'Meeting'), ('call', 'Call')],
                           default='general', validators=[DataRequired()])
    
    # Scheduling
    due_date = DateTimeField('Due Date', validators=[Optional()], format='%Y-%m-%d %H:%M')
    reminder_date = DateTimeField('Reminder Date', validators=[Optional()], format='%Y-%m-%d %H:%M')
    
    # Status and priority
    status = SelectField('Status',
                        choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), 
                                ('completed', 'Completed'), ('cancelled', 'Cancelled')],
                        default='pending', validators=[DataRequired()])
    
    priority = SelectField('Priority',
                          choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
                          default='medium', validators=[DataRequired()])
    
    # Relationships
    lead_id = SelectField('Related Lead', choices=[('', 'No Lead')], validators=[Optional()], coerce=int)
    customer_id = SelectField('Related Customer', choices=[('', 'No Customer')], validators=[Optional()], coerce=int)
    opportunity_id = SelectField('Related Opportunity', choices=[('', 'No Opportunity')], validators=[Optional()], coerce=int)
    
    # Additional
    notes = TextAreaField('Notes', validators=[Optional()])
    tags = StringField('Tags (comma separated)', validators=[Optional(), Length(max=500)])
    
    def __init__(self, *args, **kwargs):
        super(CRMTaskForm, self).__init__(*args, **kwargs)
        if current_user.is_authenticated:
            # Populate relationship choices
            leads = Lead.query.filter_by(
                company_id=current_user.company_id,
                lead_status__ne='converted'
            ).order_by(Lead.first_name, Lead.last_name).all()
            self.lead_id.choices = [('', 'No Lead')] + [(l.id, l.full_name) for l in leads]
            
            customers = Customer.query.filter_by(
                company_id=current_user.company_id,
                customer_status='active'
            ).order_by(Customer.company_name, Customer.first_name).all()
            self.customer_id.choices = [('', 'No Customer')] + [(c.id, c.display_name) for c in customers]
            
            opportunities = Opportunity.query.filter_by(
                company_id=current_user.company_id,
                status='open'
            ).order_by(Opportunity.opportunity_name).all()
            self.opportunity_id.choices = [('', 'No Opportunity')] + [(o.id, o.opportunity_name) for o in opportunities]


class CRMNoteForm(FlaskForm):
    title = StringField('Note Title', validators=[Optional(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    note_type = SelectField('Note Type',
                           choices=[('general', 'General'), ('meeting', 'Meeting Notes'), 
                                   ('call', 'Call Notes'), ('research', 'Research'),
                                   ('internal', 'Internal Note')],
                           default='general', validators=[DataRequired()])
    
    # Relationships
    lead_id = SelectField('Related Lead', choices=[('', 'No Lead')], validators=[Optional()], coerce=int)
    customer_id = SelectField('Related Customer', choices=[('', 'No Customer')], validators=[Optional()], coerce=int)
    opportunity_id = SelectField('Related Opportunity', choices=[('', 'No Opportunity')], validators=[Optional()], coerce=int)
    
    # Privacy
    is_private = BooleanField('Private Note (only visible to you)')
    
    def __init__(self, *args, **kwargs):
        super(CRMNoteForm, self).__init__(*args, **kwargs)
        if current_user.is_authenticated:
            # Populate relationship choices
            leads = Lead.query.filter_by(
                company_id=current_user.company_id,
                lead_status__ne='converted'
            ).order_by(Lead.first_name, Lead.last_name).all()
            self.lead_id.choices = [('', 'No Lead')] + [(l.id, l.full_name) for l in leads]
            
            customers = Customer.query.filter_by(
                company_id=current_user.company_id,
                customer_status='active'
            ).order_by(Customer.company_name, Customer.first_name).all()
            self.customer_id.choices = [('', 'No Customer')] + [(c.id, c.display_name) for c in customers]
            
            opportunities = Opportunity.query.filter_by(
                company_id=current_user.company_id,
                status='open'
            ).order_by(Opportunity.opportunity_name).all()
            self.opportunity_id.choices = [('', 'No Opportunity')] + [(o.id, o.opportunity_name) for o in opportunities]


class CRMSearchForm(FlaskForm):
    search_type = SelectField('Search In',
                             choices=[('all', 'All Records'), ('leads', 'Leads'), 
                                     ('customers', 'Customers'), ('opportunities', 'Opportunities')],
                             default='all')
    
    search_query = StringField('Search', validators=[Optional()])
    
    # Filters
    status_filter = SelectField('Status Filter', choices=[('', 'All Statuses')], validators=[Optional()])
    date_from = DateField('From Date', validators=[Optional()])
    date_to = DateField('To Date', validators=[Optional()])
    assigned_to = SelectField('Assigned To', choices=[('', 'All Users')], validators=[Optional()], coerce=int)
    
    def __init__(self, *args, **kwargs):
        super(CRMSearchForm, self).__init__(*args, **kwargs)
        if current_user.is_authenticated:
            # Populate assigned to choices
            from models.user import User
            users = User.query.filter_by(company_id=current_user.company_id).order_by(User.username).all()
            self.assigned_to.choices = [('', 'All Users')] + [(u.id, u.username) for u in users]


class ConvertLeadForm(FlaskForm):
    """Form for converting a lead to a customer"""
    create_customer = BooleanField('Create Customer', default=True)
    create_opportunity = BooleanField('Create Opportunity', default=False)
    
    # Opportunity details (if creating opportunity)
    opportunity_name = StringField('Opportunity Name', validators=[Optional(), Length(max=200)])
    opportunity_value = FloatField('Opportunity Value', validators=[Optional(), NumberRange(min=0)])
    opportunity_stage = SelectField('Initial Stage',
                                   choices=[('prospecting', 'Prospecting'), ('qualification', 'Qualification'),
                                           ('proposal', 'Proposal')],
                                   default='qualification', validators=[Optional()])
    
    close_lead = BooleanField('Close Lead as Converted', default=True)
    conversion_notes = TextAreaField('Conversion Notes', validators=[Optional()])
