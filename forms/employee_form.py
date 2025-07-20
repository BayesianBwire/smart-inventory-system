from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, FileField, SubmitField
from wtforms.validators import DataRequired, Email

class EmployeeForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    employee_id = StringField('Employee ID', validators=[DataRequired()])
    department = StringField('Department', validators=[DataRequired()])
    designation = StringField('Designation', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female')], validators=[DataRequired()])
    dob = DateField('Date of Birth', validators=[DataRequired()])
    email = StringField('Email', validators=[Email()])
    phone = StringField('Phone')
    address = StringField('Address')
    national_id = StringField('National ID')
    joining_date = DateField('Joining Date', validators=[DataRequired()])
    employment_status = SelectField('Status', choices=[('active', 'Active'), ('on_leave', 'On Leave'), ('terminated', 'Terminated')])
    photo = FileField('Photo')
    submit = SubmitField('Submit')
