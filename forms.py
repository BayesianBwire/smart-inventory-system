from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField, DecimalField,
    IntegerField, TextAreaField, SelectField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, Optional, URL, NumberRange
)

# ✅ Registration Form
class RegisterForm(FlaskForm):
    full_name = StringField('Full Name', validators=[
        DataRequired(), Length(min=3, max=100)
    ])
    username = StringField('Username', validators=[
        DataRequired(), Length(min=3, max=80)
    ])
    email = StringField('Email', validators=[
        DataRequired(), Email(), Length(max=120)
    ])
    phone_number = StringField('Phone Number', validators=[
        Optional(), Length(min=7, max=20)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(), Length(min=6)
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match.')
    ])
    role = SelectField('Role', choices=[
        ('', 'Select Role'),
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('cashier', 'Cashier'),
        ('salesperson', 'Sales Representative'),
        ('warehouse', 'Warehouse Manager'),
        ('accountant', 'Accountant'),
        ('supervisor', 'Supervisor'),
        ('inventory_clerk', 'Inventory Clerk'),
        ('security', 'Security'),
        ('customer_service', 'Customer Service'),
        ('cleaner', 'Cleaner'),
        ('it_support', 'IT Support'),
        ('attendant', 'Attendant')
    ], validators=[DataRequired()])
    submit = SubmitField('Register')

# ✅ Login Form
class LoginForm(FlaskForm):
    username = StringField('Username or Email', validators=[
        DataRequired()
    ])
    password = PasswordField('Password', validators=[
        DataRequired()
    ])
    submit = SubmitField('Login')

# ✅ Forgot Password Form
class ForgotPasswordForm(FlaskForm):
    email = StringField('Email Address', validators=[
        DataRequired(), Email()
    ])
    submit = SubmitField('Send Reset Link')

# ✅ Reset Password Form
class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(), Length(min=6)
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Reset Password')

# ✅ Product Management Form
class ProductForm(FlaskForm):
    product_code = StringField('Product Code', validators=[DataRequired()])
    product_name = StringField('Product Name', validators=[DataRequired()])
    category = StringField('Category', validators=[DataRequired()])
    price = DecimalField('Price (KES)', validators=[DataRequired(), NumberRange(min=0)])
    cost_price = DecimalField('Cost Price (KES)', validators=[DataRequired(), NumberRange(min=0)])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    description = TextAreaField('Description', validators=[Optional()])
    image_url = StringField('Image URL', validators=[Optional(), URL()])
    average_rating = DecimalField('Average Rating', validators=[Optional(), NumberRange(min=0, max=5)], default=0.0)
    reviews_count = IntegerField('Reviews Count', validators=[Optional()], default=0)
    submit = SubmitField('Submit Product')
