from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Employee
from models.support_ticket import SupportTicket
from forms.support_ticket_form import SupportTicketForm

support_bp = Blueprint("support_bp", __name__)

@support_bp.route("/")
@login_required
def dashboard():
    """Support dashboard with ticket overview"""
    # Get recent tickets for the current company/user
    tickets = SupportTicket.query.filter_by(submitted_by_id=current_user.id).order_by(SupportTicket.date_created.desc()).limit(10).all()
    return render_template('support/dashboard.html', tickets=tickets)

@support_bp.route("/support/create", methods=["GET", "POST"])
@login_required
def create_ticket():
    form = SupportTicketForm()
    # Populate assignable staff list
    employees = Employee.query.all()
    form.assigned_staff_id.choices = [(0, "---")] + [(e.id, e.full_name) for e in employees]

    if form.validate_on_submit():
        assigned_id = form.assigned_staff_id.data if form.assigned_staff_id.data != 0 else None
        new_ticket = SupportTicket(
            submitted_by_id=current_user.id,
            subject=form.subject.data,
            description=form.description.data,
            priority=form.priority.data,
            category=form.category.data,
            status=form.status.data,
            assigned_staff_id=assigned_id
        )
        db.session.add(new_ticket)
        db.session.commit()
        flash("🎫 Support ticket submitted successfully.", "success")
        return redirect(url_for("support_bp.view_tickets"))

    return render_template("support/create.html", form=form)
