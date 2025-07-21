from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, desc, asc, or_, and_
from datetime import datetime, timedelta
from models.crm import Lead, Customer, Opportunity, CRMActivity, CRMTask, CRMNote
from models.user import User
from forms.crm_forms import (LeadForm, CustomerForm, OpportunityForm, CRMActivityForm, 
                            CRMTaskForm, CRMNoteForm, CRMSearchForm, ConvertLeadForm)
from extensions import db
import json

# Create CRM blueprint
crm_bp = Blueprint('crm', __name__, url_prefix='/crm')

# ================== DASHBOARD ==================

@crm_bp.route('/')
@login_required
def dashboard():
    """CRM Dashboard with key metrics and recent activity"""
    # Get date ranges for analytics
    today = datetime.utcnow().date()
    this_month_start = today.replace(day=1)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    
    # Lead metrics
    total_leads = Lead.query.filter_by(company_id=current_user.company_id).count()
    new_leads_this_month = Lead.query.filter(
        Lead.company_id == current_user.company_id,
        Lead.created_at >= this_month_start
    ).count()
    
    qualified_leads = Lead.query.filter(
        Lead.company_id == current_user.company_id,
        Lead.qualification_status.in_(['marketing_qualified', 'sales_qualified'])
    ).count()
    
    # Customer metrics
    total_customers = Customer.query.filter_by(company_id=current_user.company_id).count()
    active_customers = Customer.query.filter_by(
        company_id=current_user.company_id,
        customer_status='active'
    ).count()
    
    # Opportunity metrics
    open_opportunities = Opportunity.query.filter_by(
        company_id=current_user.company_id,
        status='open'
    ).all()
    
    total_pipeline_value = sum(opp.estimated_value for opp in open_opportunities)
    weighted_pipeline = sum(opp.estimated_value * (opp.probability / 100) for opp in open_opportunities)
    
    opportunities_this_month = Opportunity.query.filter(
        Opportunity.company_id == current_user.company_id,
        Opportunity.created_at >= this_month_start
    ).count()
    
    # Won/Lost opportunities this month
    won_opportunities = Opportunity.query.filter(
        Opportunity.company_id == current_user.company_id,
        Opportunity.stage == 'closed_won',
        Opportunity.updated_at >= this_month_start
    ).all()
    
    revenue_this_month = sum(opp.estimated_value for opp in won_opportunities)
    
    # Recent activities
    recent_activities = CRMActivity.query.filter_by(
        company_id=current_user.company_id
    ).order_by(desc(CRMActivity.created_at)).limit(10).all()
    
    # Upcoming tasks
    upcoming_tasks = CRMTask.query.filter(
        CRMTask.company_id == current_user.company_id,
        CRMTask.status.in_(['pending', 'in_progress']),
        CRMTask.due_date >= datetime.utcnow()
    ).order_by(CRMTask.due_date).limit(10).all()
    
    # Overdue tasks
    overdue_tasks = CRMTask.query.filter(
        CRMTask.company_id == current_user.company_id,
        CRMTask.status.in_(['pending', 'in_progress']),
        CRMTask.due_date < datetime.utcnow()
    ).count()
    
    # Sales pipeline by stage
    pipeline_data = db.session.query(
        Opportunity.stage,
        func.count(Opportunity.id).label('count'),
        func.sum(Opportunity.estimated_value).label('value')
    ).filter_by(
        company_id=current_user.company_id,
        status='open'
    ).group_by(Opportunity.stage).all()
    
    # Lead conversion rate
    converted_leads = Lead.query.filter_by(
        company_id=current_user.company_id,
        lead_status='converted'
    ).count()
    
    conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
    
    return render_template('crm/dashboard.html',
                         # Metrics
                         total_leads=total_leads,
                         new_leads_this_month=new_leads_this_month,
                         qualified_leads=qualified_leads,
                         total_customers=total_customers,
                         active_customers=active_customers,
                         total_pipeline_value=total_pipeline_value,
                         weighted_pipeline=weighted_pipeline,
                         opportunities_this_month=opportunities_this_month,
                         revenue_this_month=revenue_this_month,
                         conversion_rate=conversion_rate,
                         overdue_tasks=overdue_tasks,
                         # Data
                         recent_activities=recent_activities,
                         upcoming_tasks=upcoming_tasks,
                         pipeline_data=pipeline_data)

# ================== LEADS ==================

@crm_bp.route('/leads')
@login_required
def leads():
    """Display all leads with filtering and sorting"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Base query
    query = Lead.query.filter_by(company_id=current_user.company_id)
    
    # Filtering
    status_filter = request.args.get('status')
    if status_filter:
        query = query.filter(Lead.lead_status == status_filter)
    
    source_filter = request.args.get('source')
    if source_filter:
        query = query.filter(Lead.lead_source == source_filter)
    
    search = request.args.get('search')
    if search:
        query = query.filter(or_(
            Lead.first_name.ilike(f'%{search}%'),
            Lead.last_name.ilike(f'%{search}%'),
            Lead.company_name.ilike(f'%{search}%'),
            Lead.email.ilike(f'%{search}%')
        ))
    
    # Sorting
    sort_by = request.args.get('sort', 'created_at')
    sort_order = request.args.get('order', 'desc')
    
    if sort_order == 'desc':
        query = query.order_by(desc(getattr(Lead, sort_by)))
    else:
        query = query.order_by(asc(getattr(Lead, sort_by)))
    
    # Pagination
    leads_pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('crm/leads.html', 
                         leads=leads_pagination.items,
                         pagination=leads_pagination)

@crm_bp.route('/leads/add', methods=['GET', 'POST'])
@login_required
def add_lead():
    """Add a new lead"""
    form = LeadForm()
    
    if form.validate_on_submit():
        try:
            lead = Lead(
                company_id=current_user.company_id,
                assigned_to=current_user.id,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                company_name=form.company_name.data,
                email=form.email.data,
                phone=form.phone.data,
                mobile=form.mobile.data,
                website=form.website.data,
                address=form.address.data,
                city=form.city.data,
                state=form.state.data,
                country=form.country.data,
                postal_code=form.postal_code.data,
                lead_source=form.lead_source.data,
                lead_status=form.lead_status.data,
                priority=form.priority.data,
                industry=form.industry.data,
                job_title=form.job_title.data,
                annual_revenue=form.annual_revenue.data,
                number_of_employees=form.number_of_employees.data,
                qualification_status=form.qualification_status.data,
                budget=form.budget.data,
                timeline=form.timeline.data,
                decision_maker=form.decision_maker.data,
                next_follow_up=form.next_follow_up.data,
                notes=form.notes.data
            )
            
            # Handle tags
            if form.tags.data:
                lead.tags = form.tags.data
            
            db.session.add(lead)
            db.session.commit()
            
            # Calculate lead score
            lead.calculate_lead_score()
            db.session.commit()
            
            flash('Lead added successfully!', 'success')
            return redirect(url_for('crm.leads'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding lead: {str(e)}', 'error')
    
    return render_template('crm/add_lead.html', form=form)

@crm_bp.route('/leads/<int:id>')
@login_required
def view_lead(id):
    """View lead details"""
    lead = Lead.query.filter_by(
        id=id, 
        company_id=current_user.company_id
    ).first_or_404()
    
    # Get related activities
    activities = CRMActivity.query.filter_by(
        lead_id=id,
        company_id=current_user.company_id
    ).order_by(desc(CRMActivity.activity_date)).all()
    
    # Get related tasks
    tasks = CRMTask.query.filter_by(
        lead_id=id,
        company_id=current_user.company_id
    ).order_by(desc(CRMTask.created_at)).all()
    
    # Get related notes
    notes = CRMNote.query.filter_by(
        lead_id=id,
        company_id=current_user.company_id
    ).order_by(desc(CRMNote.created_at)).all()
    
    return render_template('crm/view_lead.html', 
                         lead=lead,
                         activities=activities,
                         tasks=tasks,
                         notes=notes)

@crm_bp.route('/leads/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_lead(id):
    """Edit lead"""
    lead = Lead.query.filter_by(
        id=id, 
        company_id=current_user.company_id
    ).first_or_404()
    
    form = LeadForm(obj=lead)
    form.lead_id = lead.id  # For validation
    
    if form.validate_on_submit():
        try:
            # Update lead fields
            form.populate_obj(lead)
            lead.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Recalculate lead score
            lead.calculate_lead_score()
            db.session.commit()
            
            flash('Lead updated successfully!', 'success')
            return redirect(url_for('crm.view_lead', id=lead.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating lead: {str(e)}', 'error')
    
    return render_template('crm/edit_lead.html', form=form, lead=lead)

@crm_bp.route('/leads/<int:id>/convert', methods=['GET', 'POST'])
@login_required
def convert_lead(id):
    """Convert lead to customer and optionally create opportunity"""
    lead = Lead.query.filter_by(
        id=id, 
        company_id=current_user.company_id
    ).first_or_404()
    
    if lead.lead_status == 'converted':
        flash('Lead has already been converted.', 'warning')
        return redirect(url_for('crm.view_lead', id=lead.id))
    
    form = ConvertLeadForm()
    
    if form.validate_on_submit():
        try:
            customer_id = None
            opportunity_id = None
            
            # Create customer
            if form.create_customer.data:
                customer = Customer(
                    company_id=current_user.company_id,
                    customer_type='individual' if not lead.company_name else 'business',
                    first_name=lead.first_name,
                    last_name=lead.last_name,
                    company_name=lead.company_name,
                    email=lead.email,
                    phone=lead.phone,
                    mobile=lead.mobile,
                    website=lead.website,
                    billing_address=lead.address,
                    billing_city=lead.city,
                    billing_state=lead.state,
                    billing_country=lead.country,
                    billing_postal_code=lead.postal_code,
                    industry=lead.industry,
                    annual_revenue=lead.annual_revenue,
                    number_of_employees=lead.number_of_employees,
                    customer_status='active',
                    notes=lead.notes
                )
                
                db.session.add(customer)
                db.session.flush()  # Get customer ID
                customer_id = customer.id
            
            # Create opportunity
            if form.create_opportunity.data and form.opportunity_name.data:
                opportunity = Opportunity(
                    company_id=current_user.company_id,
                    customer_id=customer_id,
                    assigned_to=current_user.id,
                    opportunity_name=form.opportunity_name.data,
                    estimated_value=form.opportunity_value.data or 0,
                    stage=form.opportunity_stage.data,
                    lead_source=lead.lead_source,
                    status='open'
                )
                
                db.session.add(opportunity)
                db.session.flush()
                opportunity_id = opportunity.id
            
            # Update lead status
            if form.close_lead.data:
                lead.lead_status = 'converted'
                lead.converted_at = datetime.utcnow()
                lead.customer_id = customer_id
                lead.updated_at = datetime.utcnow()
                
                # Add conversion note
                if form.conversion_notes.data:
                    lead.notes = (lead.notes or '') + f"\n\nConversion Notes ({datetime.utcnow().strftime('%Y-%m-%d')}): {form.conversion_notes.data}"
            
            db.session.commit()
            
            flash('Lead converted successfully!', 'success')
            
            if customer_id:
                return redirect(url_for('crm.view_customer', id=customer_id))
            else:
                return redirect(url_for('crm.view_lead', id=lead.id))
                
        except Exception as e:
            db.session.rollback()
            flash(f'Error converting lead: {str(e)}', 'error')
    
    return render_template('crm/convert_lead.html', form=form, lead=lead)

# ================== CUSTOMERS ==================

@crm_bp.route('/customers')
@login_required
def customers():
    """Display all customers with filtering and sorting"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Base query
    query = Customer.query.filter_by(company_id=current_user.company_id)
    
    # Filtering
    status_filter = request.args.get('status')
    if status_filter:
        query = query.filter(Customer.customer_status == status_filter)
    
    type_filter = request.args.get('type')
    if type_filter:
        query = query.filter(Customer.customer_type == type_filter)
    
    search = request.args.get('search')
    if search:
        query = query.filter(or_(
            Customer.first_name.ilike(f'%{search}%'),
            Customer.last_name.ilike(f'%{search}%'),
            Customer.company_name.ilike(f'%{search}%'),
            Customer.email.ilike(f'%{search}%')
        ))
    
    # Sorting
    sort_by = request.args.get('sort', 'created_at')
    sort_order = request.args.get('order', 'desc')
    
    if sort_order == 'desc':
        query = query.order_by(desc(getattr(Customer, sort_by)))
    else:
        query = query.order_by(asc(getattr(Customer, sort_by)))
    
    # Pagination
    customers_pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('crm/customers.html', 
                         customers=customers_pagination.items,
                         pagination=customers_pagination)

@crm_bp.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    """Add a new customer"""
    form = CustomerForm()
    
    if form.validate_on_submit():
        try:
            customer = Customer(
                company_id=current_user.company_id,
                customer_type=form.customer_type.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                company_name=form.company_name.data,
                business_type=form.business_type.data,
                tax_id=form.tax_id.data,
                registration_number=form.registration_number.data,
                email=form.email.data,
                phone=form.phone.data,
                mobile=form.mobile.data,
                website=form.website.data,
                billing_address=form.billing_address.data,
                billing_city=form.billing_city.data,
                billing_state=form.billing_state.data,
                billing_country=form.billing_country.data,
                billing_postal_code=form.billing_postal_code.data,
                shipping_address=form.shipping_address.data,
                shipping_city=form.shipping_city.data,
                shipping_state=form.shipping_state.data,
                shipping_country=form.shipping_country.data,
                shipping_postal_code=form.shipping_postal_code.data,
                customer_status=form.customer_status.data,
                customer_segment=form.customer_segment.data,
                industry=form.industry.data,
                annual_revenue=form.annual_revenue.data,
                number_of_employees=form.number_of_employees.data,
                credit_limit=form.credit_limit.data,
                payment_terms=form.payment_terms.data,
                preferred_payment_method=form.preferred_payment_method.data,
                email_opt_in=form.email_opt_in.data,
                sms_opt_in=form.sms_opt_in.data,
                marketing_opt_in=form.marketing_opt_in.data,
                preferred_contact_method=form.preferred_contact_method.data,
                notes=form.notes.data
            )
            
            # Handle tags
            if form.tags.data:
                customer.tags = form.tags.data
            
            db.session.add(customer)
            db.session.commit()
            
            flash('Customer added successfully!', 'success')
            return redirect(url_for('crm.customers'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding customer: {str(e)}', 'error')
    
    return render_template('crm/add_customer.html', form=form)

@crm_bp.route('/customers/<int:id>')
@login_required
def view_customer(id):
    """View customer details"""
    customer = Customer.query.filter_by(
        id=id, 
        company_id=current_user.company_id
    ).first_or_404()
    
    # Get related opportunities
    opportunities = Opportunity.query.filter_by(
        customer_id=id,
        company_id=current_user.company_id
    ).order_by(desc(Opportunity.created_at)).all()
    
    # Get related activities
    activities = CRMActivity.query.filter_by(
        customer_id=id,
        company_id=current_user.company_id
    ).order_by(desc(CRMActivity.activity_date)).limit(20).all()
    
    # Get related tasks
    tasks = CRMTask.query.filter_by(
        customer_id=id,
        company_id=current_user.company_id
    ).order_by(desc(CRMTask.created_at)).limit(10).all()
    
    # Get related notes
    notes = CRMNote.query.filter_by(
        customer_id=id,
        company_id=current_user.company_id
    ).order_by(desc(CRMNote.created_at)).limit(10).all()
    
    return render_template('crm/view_customer.html', 
                         customer=customer,
                         opportunities=opportunities,
                         activities=activities,
                         tasks=tasks,
                         notes=notes)

@crm_bp.route('/customers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    """Edit customer"""
    customer = Customer.query.filter_by(
        id=id, 
        company_id=current_user.company_id
    ).first_or_404()
    
    form = CustomerForm(obj=customer)
    form.customer_id = customer.id  # For validation
    
    if form.validate_on_submit():
        try:
            # Update customer fields
            form.populate_obj(customer)
            customer.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash('Customer updated successfully!', 'success')
            return redirect(url_for('crm.view_customer', id=customer.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating customer: {str(e)}', 'error')
    
    return render_template('crm/edit_customer.html', form=form, customer=customer)

# ================== OPPORTUNITIES ==================

@crm_bp.route('/opportunities')
@login_required
def opportunities():
    """Display all opportunities with filtering and sorting"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Base query
    query = Opportunity.query.filter_by(company_id=current_user.company_id)
    
    # Filtering
    stage_filter = request.args.get('stage')
    if stage_filter:
        query = query.filter(Opportunity.stage == stage_filter)
    
    status_filter = request.args.get('status')
    if status_filter:
        query = query.filter(Opportunity.status == status_filter)
    
    search = request.args.get('search')
    if search:
        query = query.filter(or_(
            Opportunity.opportunity_name.ilike(f'%{search}%'),
            Opportunity.description.ilike(f'%{search}%')
        ))
    
    # Sorting
    sort_by = request.args.get('sort', 'created_at')
    sort_order = request.args.get('order', 'desc')
    
    if sort_order == 'desc':
        query = query.order_by(desc(getattr(Opportunity, sort_by)))
    else:
        query = query.order_by(asc(getattr(Opportunity, sort_by)))
    
    # Pagination
    opportunities_pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('crm/opportunities.html', 
                         opportunities=opportunities_pagination.items,
                         pagination=opportunities_pagination)

@crm_bp.route('/opportunities/add', methods=['GET', 'POST'])
@login_required
def add_opportunity():
    """Add a new opportunity"""
    form = OpportunityForm()
    
    if form.validate_on_submit():
        try:
            opportunity = Opportunity(
                company_id=current_user.company_id,
                customer_id=form.customer_id.data,
                assigned_to=current_user.id,
                opportunity_name=form.opportunity_name.data,
                description=form.description.data,
                contact_person=form.contact_person.data,
                opportunity_type=form.opportunity_type.data,
                lead_source=form.lead_source.data,
                estimated_value=form.estimated_value.data,
                probability=form.probability.data,
                stage=form.stage.data,
                expected_close_date=form.expected_close_date.data,
                priority=form.priority.data,
                next_action=form.next_action.data,
                next_action_date=form.next_action_date.data,
                notes=form.notes.data,
                status='open'
            )
            
            # Handle tags
            if form.tags.data:
                opportunity.tags = form.tags.data
            
            db.session.add(opportunity)
            db.session.commit()
            
            flash('Opportunity added successfully!', 'success')
            return redirect(url_for('crm.opportunities'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding opportunity: {str(e)}', 'error')
    
    return render_template('crm/add_opportunity.html', form=form)

@crm_bp.route('/opportunities/<int:id>')
@login_required
def view_opportunity(id):
    """View opportunity details"""
    opportunity = Opportunity.query.filter_by(
        id=id, 
        company_id=current_user.company_id
    ).first_or_404()
    
    # Get related activities
    activities = CRMActivity.query.filter_by(
        opportunity_id=id,
        company_id=current_user.company_id
    ).order_by(desc(CRMActivity.activity_date)).all()
    
    # Get related tasks
    tasks = CRMTask.query.filter_by(
        opportunity_id=id,
        company_id=current_user.company_id
    ).order_by(desc(CRMTask.created_at)).all()
    
    # Get related notes
    notes = CRMNote.query.filter_by(
        opportunity_id=id,
        company_id=current_user.company_id
    ).order_by(desc(CRMNote.created_at)).all()
    
    return render_template('crm/view_opportunity.html', 
                         opportunity=opportunity,
                         activities=activities,
                         tasks=tasks,
                         notes=notes)

@crm_bp.route('/opportunities/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_opportunity(id):
    """Edit opportunity"""
    opportunity = Opportunity.query.filter_by(
        id=id, 
        company_id=current_user.company_id
    ).first_or_404()
    
    form = OpportunityForm(obj=opportunity)
    
    if form.validate_on_submit():
        try:
            # Update opportunity fields
            form.populate_obj(opportunity)
            opportunity.updated_at = datetime.utcnow()
            
            # Close opportunity if stage is won/lost
            if opportunity.stage in ['closed_won', 'closed_lost']:
                opportunity.status = 'closed'
                opportunity.actual_close_date = datetime.utcnow().date()
            
            db.session.commit()
            
            flash('Opportunity updated successfully!', 'success')
            return redirect(url_for('crm.view_opportunity', id=opportunity.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating opportunity: {str(e)}', 'error')
    
    return render_template('crm/edit_opportunity.html', form=form, opportunity=opportunity)

# ================== ACTIVITIES ==================

@crm_bp.route('/activities')
@login_required
def activities():
    """Display all CRM activities"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Base query
    query = CRMActivity.query.filter_by(company_id=current_user.company_id)
    
    # Filtering
    type_filter = request.args.get('type')
    if type_filter:
        query = query.filter(CRMActivity.activity_type == type_filter)
    
    status_filter = request.args.get('status')
    if status_filter:
        query = query.filter(CRMActivity.status == status_filter)
    
    # Sorting
    sort_order = request.args.get('order', 'desc')
    if sort_order == 'desc':
        query = query.order_by(desc(CRMActivity.activity_date))
    else:
        query = query.order_by(asc(CRMActivity.activity_date))
    
    # Pagination
    activities_pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('crm/activities.html', 
                         activities=activities_pagination.items,
                         pagination=activities_pagination)

@crm_bp.route('/activities/add', methods=['GET', 'POST'])
@login_required
def add_activity():
    """Add a new CRM activity"""
    form = CRMActivityForm()
    
    if form.validate_on_submit():
        try:
            activity = CRMActivity(
                company_id=current_user.company_id,
                created_by=current_user.id,
                activity_type=form.activity_type.data,
                subject=form.subject.data,
                description=form.description.data,
                activity_date=form.activity_date.data,
                due_date=form.due_date.data,
                duration=form.duration.data,
                status=form.status.data,
                priority=form.priority.data,
                lead_id=form.lead_id.data if form.lead_id.data else None,
                customer_id=form.customer_id.data if form.customer_id.data else None,
                opportunity_id=form.opportunity_id.data if form.opportunity_id.data else None,
                outcome=form.outcome.data,
                follow_up_required=form.follow_up_required.data,
                follow_up_date=form.follow_up_date.data,
                location=form.location.data,
                participants=form.participants.data
            )
            
            # Handle tags
            if form.tags.data:
                activity.tags = form.tags.data
            
            db.session.add(activity)
            db.session.commit()
            
            flash('Activity added successfully!', 'success')
            return redirect(url_for('crm.activities'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding activity: {str(e)}', 'error')
    
    return render_template('crm/add_activity.html', form=form)

@crm_bp.route('/activities/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_activity(id):
    """Edit CRM activity"""
    activity = CRMActivity.query.filter_by(
        id=id, 
        company_id=current_user.company_id
    ).first_or_404()
    
    form = CRMActivityForm(obj=activity)
    
    if form.validate_on_submit():
        try:
            # Update activity fields
            form.populate_obj(activity)
            activity.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash('Activity updated successfully!', 'success')
            return redirect(url_for('crm.activities'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating activity: {str(e)}', 'error')
    
    return render_template('crm/edit_activity.html', form=form, activity=activity)

# ================== TASKS ==================

@crm_bp.route('/tasks')
@login_required
def tasks():
    """Display all CRM tasks"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Base query
    query = CRMTask.query.filter_by(company_id=current_user.company_id)
    
    # Filtering
    status_filter = request.args.get('status')
    if status_filter:
        query = query.filter(CRMTask.status == status_filter)
    
    priority_filter = request.args.get('priority')
    if priority_filter:
        query = query.filter(CRMTask.priority == priority_filter)
    
    # Show only my tasks if requested
    my_tasks = request.args.get('my_tasks')
    if my_tasks == '1':
        query = query.filter(CRMTask.assigned_to == current_user.id)
    
    # Sorting
    sort_by = request.args.get('sort', 'due_date')
    sort_order = request.args.get('order', 'asc')
    
    if sort_order == 'desc':
        query = query.order_by(desc(getattr(CRMTask, sort_by)))
    else:
        query = query.order_by(asc(getattr(CRMTask, sort_by)))
    
    # Pagination
    tasks_pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('crm/tasks.html', 
                         tasks=tasks_pagination.items,
                         pagination=tasks_pagination)

@crm_bp.route('/tasks/add', methods=['GET', 'POST'])
@login_required
def add_task():
    """Add a new CRM task"""
    form = CRMTaskForm()
    
    if form.validate_on_submit():
        try:
            task = CRMTask(
                company_id=current_user.company_id,
                assigned_to=current_user.id,
                created_by=current_user.id,
                title=form.title.data,
                description=form.description.data,
                task_type=form.task_type.data,
                due_date=form.due_date.data,
                reminder_date=form.reminder_date.data,
                status=form.status.data,
                priority=form.priority.data,
                lead_id=form.lead_id.data if form.lead_id.data else None,
                customer_id=form.customer_id.data if form.customer_id.data else None,
                opportunity_id=form.opportunity_id.data if form.opportunity_id.data else None,
                notes=form.notes.data
            )
            
            # Handle tags
            if form.tags.data:
                task.tags = form.tags.data
            
            db.session.add(task)
            db.session.commit()
            
            flash('Task added successfully!', 'success')
            return redirect(url_for('crm.tasks'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding task: {str(e)}', 'error')
    
    return render_template('crm/add_task.html', form=form)

@crm_bp.route('/tasks/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(id):
    """Edit CRM task"""
    task = CRMTask.query.filter_by(
        id=id, 
        company_id=current_user.company_id
    ).first_or_404()
    
    form = CRMTaskForm(obj=task)
    
    if form.validate_on_submit():
        try:
            # Update task fields
            form.populate_obj(task)
            task.updated_at = datetime.utcnow()
            
            # Set completion date if status is completed
            if task.status == 'completed' and not task.completed_at:
                task.completed_at = datetime.utcnow()
            elif task.status != 'completed':
                task.completed_at = None
            
            db.session.commit()
            
            flash('Task updated successfully!', 'success')
            return redirect(url_for('crm.tasks'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating task: {str(e)}', 'error')
    
    return render_template('crm/edit_task.html', form=form, task=task)

@crm_bp.route('/tasks/<int:id>/complete', methods=['POST'])
@login_required
def complete_task(id):
    """Mark task as completed"""
    task = CRMTask.query.filter_by(
        id=id, 
        company_id=current_user.company_id
    ).first_or_404()
    
    try:
        task.status = 'completed'
        task.completed_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Task marked as completed!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error completing task: {str(e)}', 'error')
    
    return redirect(url_for('crm.tasks'))

# ================== NOTES ==================

@crm_bp.route('/notes/add', methods=['GET', 'POST'])
@login_required
def add_note():
    """Add a new CRM note"""
    form = CRMNoteForm()
    
    if form.validate_on_submit():
        try:
            note = CRMNote(
                company_id=current_user.company_id,
                created_by=current_user.id,
                title=form.title.data,
                content=form.content.data,
                note_type=form.note_type.data,
                lead_id=form.lead_id.data if form.lead_id.data else None,
                customer_id=form.customer_id.data if form.customer_id.data else None,
                opportunity_id=form.opportunity_id.data if form.opportunity_id.data else None,
                is_private=form.is_private.data
            )
            
            db.session.add(note)
            db.session.commit()
            
            flash('Note added successfully!', 'success')
            
            # Redirect to related record if available
            if note.customer_id:
                return redirect(url_for('crm.view_customer', id=note.customer_id))
            elif note.lead_id:
                return redirect(url_for('crm.view_lead', id=note.lead_id))
            elif note.opportunity_id:
                return redirect(url_for('crm.view_opportunity', id=note.opportunity_id))
            else:
                return redirect(url_for('crm.dashboard'))
                
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding note: {str(e)}', 'error')
    
    # Pre-populate form if related record is specified
    lead_id = request.args.get('lead_id', type=int)
    customer_id = request.args.get('customer_id', type=int)
    opportunity_id = request.args.get('opportunity_id', type=int)
    
    if lead_id:
        form.lead_id.data = lead_id
    elif customer_id:
        form.customer_id.data = customer_id
    elif opportunity_id:
        form.opportunity_id.data = opportunity_id
    
    return render_template('crm/add_note.html', form=form)

# ================== API ENDPOINTS ==================

@crm_bp.route('/api/pipeline-data')
@login_required
def api_pipeline_data():
    """API endpoint for pipeline chart data"""
    pipeline_data = db.session.query(
        Opportunity.stage,
        func.count(Opportunity.id).label('count'),
        func.sum(Opportunity.estimated_value).label('value')
    ).filter_by(
        company_id=current_user.company_id,
        status='open'
    ).group_by(Opportunity.stage).all()
    
    result = []
    for item in pipeline_data:
        result.append({
            'stage': item.stage.replace('_', ' ').title(),
            'count': item.count,
            'value': float(item.value or 0)
        })
    
    return jsonify(result)

@crm_bp.route('/api/lead-sources')
@login_required
def api_lead_sources():
    """API endpoint for lead source data"""
    source_data = db.session.query(
        Lead.lead_source,
        func.count(Lead.id).label('count')
    ).filter_by(
        company_id=current_user.company_id
    ).group_by(Lead.lead_source).all()
    
    result = []
    for item in source_data:
        if item.lead_source:
            result.append({
                'source': item.lead_source.replace('_', ' ').title(),
                'count': item.count
            })
    
    return jsonify(result)

@crm_bp.route('/api/revenue-trend')
@login_required
def api_revenue_trend():
    """API endpoint for revenue trend data"""
    # Get last 12 months of won opportunities
    months_data = []
    for i in range(12):
        date = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
        month_start = date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        revenue = db.session.query(func.sum(Opportunity.estimated_value)).filter(
            Opportunity.company_id == current_user.company_id,
            Opportunity.stage == 'closed_won',
            Opportunity.actual_close_date >= month_start.date(),
            Opportunity.actual_close_date <= month_end.date()
        ).scalar() or 0
        
        months_data.append({
            'month': month_start.strftime('%b %Y'),
            'revenue': float(revenue)
        })
    
    return jsonify(list(reversed(months_data)))

# ================== SEARCH ==================

@crm_bp.route('/search')
@login_required
def search():
    """Global CRM search"""
    form = CRMSearchForm()
    results = {
        'leads': [],
        'customers': [],
        'opportunities': []
    }
    
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')
    
    if query:
        # Search leads
        if search_type in ['all', 'leads']:
            leads = Lead.query.filter(
                Lead.company_id == current_user.company_id,
                or_(
                    Lead.first_name.ilike(f'%{query}%'),
                    Lead.last_name.ilike(f'%{query}%'),
                    Lead.company_name.ilike(f'%{query}%'),
                    Lead.email.ilike(f'%{query}%'),
                    Lead.notes.ilike(f'%{query}%')
                )
            ).limit(10).all()
            results['leads'] = leads
        
        # Search customers
        if search_type in ['all', 'customers']:
            customers = Customer.query.filter(
                Customer.company_id == current_user.company_id,
                or_(
                    Customer.first_name.ilike(f'%{query}%'),
                    Customer.last_name.ilike(f'%{query}%'),
                    Customer.company_name.ilike(f'%{query}%'),
                    Customer.email.ilike(f'%{query}%'),
                    Customer.notes.ilike(f'%{query}%')
                )
            ).limit(10).all()
            results['customers'] = customers
        
        # Search opportunities
        if search_type in ['all', 'opportunities']:
            opportunities = Opportunity.query.filter(
                Opportunity.company_id == current_user.company_id,
                or_(
                    Opportunity.opportunity_name.ilike(f'%{query}%'),
                    Opportunity.description.ilike(f'%{query}%'),
                    Opportunity.notes.ilike(f'%{query}%')
                )
            ).limit(10).all()
            results['opportunities'] = opportunities
    
    return render_template('crm/search.html', form=form, results=results, query=query)
