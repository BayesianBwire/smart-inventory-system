# routes/employee_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash
from forms.employee_form import EmployeeForm
from models.employee import Employee
from extensions import db

employee_bp = Blueprint('employee', __name__)

@employee_bp.route('/employees', methods=['GET', 'POST'])
def manage_employees():
    form = EmployeeForm()
    if form.validate_on_submit():
        new_employee = Employee(
            full_name=form.full_name.data,
            email=form.email.data,
            # Add other fields here...
        )
        db.session.add(new_employee)
        db.session.commit()
        flash("✅ Employee added successfully.", "success")
        return redirect(url_for('employee.manage_employees'))

    return render_template('employees.html', form=form)
