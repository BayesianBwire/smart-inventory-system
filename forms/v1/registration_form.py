# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError
import re

class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_password(self, field):
        password = field.data
        email = self.email.data

        if email and password.lower() == email.lower():
            raise ValidationError('Password should not match your email.')

        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long.')

        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must contain at least one uppercase letter.')

        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must contain at least one lowercase letter.')

        if not re.search(r'\d', password):
            raise ValidationError('Password must contain at least one digit.')

        if not re.search(r'[@#$%^&+=!]', password):
            raise ValidationError('Password must contain at least one special character.')
