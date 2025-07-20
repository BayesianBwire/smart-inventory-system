from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from app import app  # Import the Flask app instance

# Lead imports
from forms.lead_form import LeadForm
from models.lead import Lead

# Contact imports
from forms.contact_form import ContactForm
from models.contact import Contact

# Company imports
from forms.company_form import CompanyForm
from models.company import Company

# Deal imports
from forms.deal_form import DealForm
from models.deal import Deal

# Task imports
from forms.task_form import TaskForm
from models.task import Task

# -------------------- Lead Route --------------------
@app.route('/crm/leads/new', methods=['GET', 'POST'])
@login_required
def add_lead():
    form = LeadForm()
    if form.validate_on_submit():
        lead = Lead(
            full_name=form.full_name.data,
            email=form.email.data,
            phone=form.phone.data,
            company=form.company.data,
            lead_source=form.lead_source.data,
            lead_status=form.lead_status.data,
            industry=form.industry.data,
            notes=form.notes.data,
            user_id=current_user.id
        )
        db.session.add(lead)
        db.session.commit()
        flash("✅ Lead saved successfully!", "success")
        return redirect(url_for('add_lead'))  # reloads the form
    return render_template('crm/add_lead.html', form=form)

# -------------------- Contact Route --------------------
@app.route('/crm/contacts/new', methods=['GET', 'POST'])
@login_required
def add_contact():
    form = ContactForm()
    if form.validate_on_submit():
        contact = Contact(
            full_name=form.full_name.data,
            email=form.email.data,
            phone=form.phone.data,
            company=form.company.data,
            title=form.title.data,
            notes=form.notes.data
        )
        db.session.add(contact)
        db.session.commit()
        flash("✅ Contact saved successfully!", "success")
        return redirect(url_for('add_contact'))  # reloads the form
    return render_template('crm/add_contact.html', form=form)

# -------------------- Company Route --------------------
@app.route('/crm/companies/new', methods=['GET', 'POST'])
@login_required
def add_company():
    form = CompanyForm()
    if form.validate_on_submit():
        company = Company(
            name=form.name.data,
            address=form.address.data,
            phone=form.phone.data
        )
        db.session.add(company)
        db.session.commit()
        flash("🏢 Company registered successfully!", "success")
        return redirect(url_for('add_company'))
    return render_template('crm/add_company.html', form=form)

@app.route('/crm/deals/new', methods=['GET', 'POST'])
@login_required
def add_deal():
    form = DealForm()
    if form.validate_on_submit():
        deal = Deal(
            title=form.title.data,
            value=form.value.data,
            stage=form.stage.data,
            status=form.status.data,
            contact_name=form.contact_name.data,
            expected_close_date=form.expected_close_date.data,
            notes=form.notes.data
        )
        db.session.add(deal)
        db.session.commit()
        flash("💰 Deal saved successfully!", "success")
        return redirect(url_for('add_deal'))  # Reloads form
    return render_template('crm/add_deal.html', form=form)

@app.route('/crm/tasks/new', methods=['GET', 'POST'])
@login_required
def add_task():
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            status=form.status.data,
            priority=form.priority.data,
            related_to=form.related_to.data
        )
        db.session.add(task)
        db.session.commit()
        flash("📌 Task added successfully!", "success")
        return redirect(url_for('add_task'))
    return render_template('crm/add_task.html', form=form)

@app.route('/crm/deals/pipeline')
@login_required
def deal_pipeline():
    stages = ["Prospecting", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]

    # Group deals by stage
    pipeline = {}
    for stage in stages:
        pipeline[stage] = Deal.query.filter_by(stage=stage).all()

    return render_template("crm/deal_pipeline.html", pipeline=pipeline, stages=stages)

@app.route('/crm/deals/update_stage', methods=['POST'])
@login_required
def update_deal_stage():
    data = request.get_json()
    deal_id = data.get('deal_id')
    new_stage = data.get('new_stage')

    deal = Deal.query.get(deal_id)
    if not deal:
        return jsonify({'success': False, 'message': 'Deal not found'})

    deal.stage = new_stage
    db.session.commit()
    return jsonify({'success': True})

@app.route('/contacts/new', methods=['GET', 'POST'])  # or use a Blueprint
@login_required
def new_contact():
    form = ContactForm()
    if form.validate_on_submit():
        contact = Contact(
            full_name=form.full_name.data,
            email=form.email.data,
            phone=form.phone.data,
            company=form.company.data,
            title=form.title.data,
            notes=form.notes.data,
            user_id=current_user.id  # ✅ Important
        )
        db.session.add(contact)
        db.session.commit()
        flash('✅ Contact added successfully.', 'success')
        return redirect(url_for('contact_list'))  # Update this to your contact list route
    return render_template('contacts/new.html', form=form)

@crm.route('/dashboard')
@login_required
def crm_dashboard():
    user_id = current_user.id
    deals_count = Deal.query.filter_by(user_id=user_id).count()
    tasks_count = Task.query.filter_by(user_id=user_id).count()
    contacts_count = Contact.query.filter_by(user_id=user_id).count()

    return render_template('crm/dashboard.html', 
                           deals_count=deals_count, 
                           tasks_count=tasks_count, 
                           contacts_count=contacts_count)

@crm.route('/add_contact', methods=['GET', 'POST'])
@login_required  # if you're using Flask-Login
def add_contact():
    form = ContactForm()
    if form.validate_on_submit():
        new_contact = Contact(
            full_name=form.full_name.data,
            email=form.email.data,
            phone=form.phone.data,
            company=form.company.data,
            title=form.title.data,
            notes=form.notes.data,
            user_id=current_user.id  # <-- ✅ attach to logged-in user
        )
        db.session.add(new_contact)
        db.session.commit()
        flash("✅ Contact added successfully", "success")
        return redirect(url_for('crm.crm_dashboard'))  # or contacts list
    return render_template('crm/add_contact.html', form=form)
