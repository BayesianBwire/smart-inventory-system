from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, Length, Optional

class UserForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired()])
    username = StringField("Username", validators=[DataRequired(), Length(min=3)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone_number = StringField("Phone Number", validators=[Optional()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    role = SelectField("Role", choices=[
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('hr', 'HR'),
        ('supervisor', 'Supervisor'),
        ('attendant', 'Attendant'),
        ('sales', 'Sales'),
        ('finance', 'Finance'),
        ('support', 'Support'),
        ('it', 'IT')
    ])
    is_active = BooleanField("Active", default=True)
