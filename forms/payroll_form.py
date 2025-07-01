from flask_wtf import FlaskForm
from wtforms import FloatField, SubmitField, DateField, FileField, StringField
from wtforms.validators import DataRequired, Optional
from wtforms_sqlalchemy.fields import QuerySelectField
from models.employee import Employee
from flask_wtf.file import FileAllowed

def get_employees():
    return Employee.query.all()

class PayrollForm(FlaskForm):
    employee = QuerySelectField(
        "Select Employee",
        query_factory=get_employees,
        get_label="full_name",
        allow_blank=False,
        validators=[DataRequired()]
    )

    basic_salary = FloatField("Basic Salary (KES)", validators=[DataRequired()])
    allowances = FloatField("Allowances (KES)", default=0.0, validators=[Optional()])
    deductions = FloatField("Deductions (KES)", default=0.0, validators=[Optional()])
    bonus = FloatField("Bonus (KES)", default=0.0, validators=[Optional()])

    net_pay = FloatField(
        "Net Pay (Auto-calculated)",
        render_kw={'readonly': True},
        description="This field will be auto-calculated based on salary and adjustments."
    )

    month = StringField("Payroll Month", validators=[DataRequired()], description="e.g. July 2025")
    payment_date = DateField("Payment Date", validators=[Optional()])
    
    remarks = StringField("Remarks / Notes", validators=[Optional()])
    
    payslip_file = FileField("Payslip Upload (PDF)", validators=[
        Optional(),
        FileAllowed(['pdf'], 'PDF files only!')
    ])

    submit = SubmitField("Submit Payroll")
