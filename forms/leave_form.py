from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, StringField, SubmitField
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Optional
from models.employee import Employee

def get_employees():
    return Employee.query.all()

class LeaveRequestForm(FlaskForm):
    employee = QuerySelectField(
        "Select Employee",
        query_factory=get_employees,
        get_label="full_name",
        allow_blank=False,
        validators=[DataRequired()]
    )

    leave_type = SelectField(
        "Leave Type",
        choices=[
            ('Sick', 'Sick'),
            ('Casual', 'Casual'),
            ('Maternity', 'Maternity'),
            ('Paternity', 'Paternity'),
            ('Study', 'Study'),
            ('Bereavement', 'Bereavement'),
        ],
        validators=[DataRequired()]
    )

    start_date = DateField("Start Date", validators=[DataRequired()])
    end_date = DateField("End Date", validators=[DataRequired()])
    reason = StringField("Reason", validators=[Optional()])
    
    status = SelectField(
        "Status",
        choices=[
            ('Pending', 'Pending'),
            ('Approved', 'Approved'),
            ('Rejected', 'Rejected')
        ],
        default='Pending',
        validators=[DataRequired()]
    )

    submit = SubmitField("Submit Leave Request")
