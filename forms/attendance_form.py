from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, TimeField, SubmitField
from wtforms.validators import DataRequired
from wtforms_sqlalchemy.fields import QuerySelectField
from models import Employee  # Adjust import if needed

class AttendanceForm(FlaskForm):
    employee = QuerySelectField(
        "Select Employee",
        query_factory=lambda: Employee.query.all(),
        get_label="full_name",
        validators=[DataRequired()]
    )
    date = DateField("Date", format='%Y-%m-%d', validators=[DataRequired()])
    check_in = TimeField("Check-in Time", validators=[DataRequired()])
    check_out = TimeField("Check-out Time", validators=[DataRequired()])
    status = SelectField(
        "Status",
        choices=[
            ("Present", "Present"),
            ("Absent", "Absent"),
            ("Leave", "Leave"),
            ("Late", "Late")
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField("Submit")