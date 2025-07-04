from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import db, LeaveRequest
from forms.leave_form import LeaveRequestForm

leave_bp = Blueprint("leave_bp", __name__)

# -------------------- DASHBOARD --------------------
@leave_bp.route("/hr/leave_dashboard")
@login_required
def leave_dashboard():
    leave_requests = LeaveRequest.query.order_by(LeaveRequest.start_date.desc()).all()
    return render_template("leave/dashboard.html", leave_requests=leave_requests)

# -------------------- CREATE REQUEST --------------------
@leave_bp.route("/leave/request", methods=["GET", "POST"])
@login_required
def leave_request():
    form = LeaveRequestForm()
    if form.validate_on_submit():
        leave = LeaveRequest(
            employee_id=form.employee.data.id,
            leave_type=form.leave_type.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            reason=form.reason.data,
            status=form.status.data
        )
        db.session.add(leave)
        db.session.commit()
        flash("✅ Leave request submitted successfully.", "success")
        return redirect(url_for("leave_bp.leave_dashboard"))

    return render_template("leave/form.html", form=form)

# -------------------- APPROVE --------------------
@leave_bp.route("/leave/<int:leave_id>/approve", methods=["POST"])
@login_required
def approve_leave(leave_id):
    leave = LeaveRequest.query.get_or_404(leave_id)
    leave.status = "Approved"
    db.session.commit()
    flash("✅ Leave approved.", "success")
    return redirect(url_for("leave_bp.leave_dashboard"))

# -------------------- REJECT --------------------
@leave_bp.route("/leave/<int:leave_id>/reject", methods=["POST"])
@login_required
def reject_leave(leave_id):
    leave = LeaveRequest.query.get_or_404(leave_id)
    leave.status = "Rejected"
    db.session.commit()
    flash("❌ Leave rejected.", "danger")
    return redirect(url_for("leave_bp.leave_dashboard"))
