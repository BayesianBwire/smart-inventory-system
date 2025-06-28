from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField, DecimalField,
    IntegerField, TextAreaField, SelectField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, Optional, URL, NumberRange
)

# --------------------------
# 🔐 Authentication Forms
# --------------------------

class RegisterForm(FlaskForm):
    full_name = StringField('Full Name', validators=[
        DataRequired(), Length(min=3, max=100)
    ], render_kw={"placeholder": "John Doe"})

    username = StringField('Username', validators=[
        DataRequired(), Length(min=3, max=80)
    ], render_kw={"placeholder": "johndoe"})

    email = StringField('Email', validators=[
        DataRequired(), Email(), Length(max=120)
    ], render_kw={"placeholder": "user@example.com"})

    phone_number = StringField('Phone Number', validators=[
        Optional(), Length(min=7, max=20)
    ], render_kw={"placeholder": "+254712345678"})

    password = PasswordField('Password', validators=[
        DataRequired(), Length(min=6)
    ], render_kw={"placeholder": "Enter password"})

    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match.')
    ], render_kw={"placeholder": "Repeat password"})

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


class LoginForm(FlaskForm):
    username = StringField('Username or Email', validators=[
        DataRequired()
    ], render_kw={"placeholder": "Enter your username or email"})

    password = PasswordField('Password', validators=[
        DataRequired()
    ], render_kw={"placeholder": "Enter your password"})

    submit = SubmitField('Login')


class ForgotPasswordForm(FlaskForm):
    email = StringField('Email Address', validators=[
        DataRequired(), Email()
    ], render_kw={"placeholder": "Enter your registered email"})

    submit = SubmitField('Send Reset Link')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(), Length(min=6)
    ], render_kw={"placeholder": "New password"})

    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match.')
    ], render_kw={"placeholder": "Repeat new password"})

    submit = SubmitField('Reset Password')

# --------------------------
# 💰 Finance Module Forms
# --------------------------

class BankAccountForm(FlaskForm):
    name = StringField('Account Name', validators=[DataRequired()])
    bank_name = StringField('Bank Name', validators=[DataRequired()])
    account_number = StringField('Account Number', validators=[Optional()])
    account_type = SelectField('Account Type', choices=[
        ('current', 'Current'),
        ('savings', 'Savings'),
        ('mobile', 'Mobile'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    currency = SelectField('Currency', choices=[
        ('KES', 'KES'),
        ('USD', 'USD'),
        ('EUR', 'EUR')
    ], validators=[DataRequired()])
    opening_balance = DecimalField('Opening Balance', validators=[
        DataRequired(), NumberRange(min=0)
    ])
    chart_of_accounts = StringField('Chart of Accounts', validators=[Optional()])
    submit = SubmitField('Save Account')

# --------------------------
# 📦 Inventory Module Forms
# --------------------------

class ProductForm(FlaskForm):
    product_code = StringField('Product Code', validators=[DataRequired()])
    product_name = StringField('Product Name', validators=[DataRequired()])
    category = StringField('Category', validators=[DataRequired()])
    price = DecimalField('Price (KES)', validators=[DataRequired(), NumberRange(min=0)])
    cost_price = DecimalField('Cost Price (KES)', validators=[DataRequired(), NumberRange(min=0)])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    description = TextAreaField('Description', validators=[Optional()])
    image_url = StringField('Image URL', validators=[Optional(), URL()])
    average_rating = DecimalField('Average Rating', validators=[
        Optional(), NumberRange(min=0, max=5)
    ], default=0.0)
    reviews_count = IntegerField('Reviews Count', validators=[Optional()], default=0)
    submit = SubmitField('Submit Product')
