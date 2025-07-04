import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename

from models import db
from models.payroll import Payroll
from forms.payroll_form import PayrollForm
from utils.role_required import role_required  # ✅ Add this import

payroll_bp = Blueprint("payroll_bp", __name__)

@payroll_bp.route('/payroll/create', methods=['GET', 'POST'])
@login_required
@role_required('hr')  # ✅ Only HR role allowed
def create_payroll():
    form = PayrollForm()

    if form.validate_on_submit():
        # ✅ Auto-calculate Net Pay
        net_pay = (
            form.basic_salary.data +
            form.allowances.data +
            form.bonus.data -
            form.deductions.data
        )

        # ✅ Handle Payslip File Upload (optional)
        payslip_filename = None
        if form.payslip_file.data:
            file = form.payslip_file.data
            filename = secure_filename(file.filename)
            payslip_folder = os.path.join(current_app.root_path, 'static', 'payslips')
            os.makedirs(payslip_folder, exist_ok=True)

            try:
                file_path = os.path.join(payslip_folder, filename)
                file.save(file_path)
                payslip_filename = filename
            except Exception as e:
                flash(f"⚠️ Failed to save payslip: {str(e)}", "danger")

        # ✅ Create Payroll Record
        new_payroll = Payroll(
            employee_id=form.employee.data.id,
            basic_salary=form.basic_salary.data,
            allowances=form.allowances.data,
            deductions=form.deductions.data,
            bonus=form.bonus.data,
            net_pay=net_pay,
            payment_date=form.payment_date.data,
            payslip_filename=payslip_filename,
            remarks=form.remarks.data,
            month=form.month.data
        )

        db.session.add(new_payroll)
        db.session.commit()

        flash("✅ Payroll record successfully created.", "success")
        return redirect(url_for("payroll_bp.view_payrolls"))

    return render_template("payroll/create.html", form=form)
