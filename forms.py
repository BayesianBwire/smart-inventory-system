from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DecimalField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, URL, NumberRange

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), Length(min=3, max=80)
    ])
    email = StringField('Email', validators=[
        DataRequired(), Email(), Length(max=120)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(), Length(min=6)
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Register')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(), Email()
    ])
    submit = SubmitField('Send Reset Link')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired()
    ])
    password = PasswordField('Password', validators=[
        DataRequired()
    ])
    submit = SubmitField('Login')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(), Length(min=6)
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Reset Password')

# ✅ Product Form added safely here
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
