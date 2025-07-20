from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp

class RegisterForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired()])
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone_number = StringField("Phone Number", validators=[
        DataRequired(),
        Length(min=10, max=15),
        Regexp(r'^\+?\d{10,15}$', message="Enter a valid phone number.")
    ])
    role = SelectField("Role", choices=[
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('staff', 'Staff')
    ], validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField("Register")
