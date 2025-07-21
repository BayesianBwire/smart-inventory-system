from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, PasswordField
from wtforms.validators import DataRequired, Length, Email, EqualTo

class CompanyForm(FlaskForm):
    # Company Information
    name = StringField('Company Name', validators=[DataRequired(), Length(max=150)])
    email = StringField('Company Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone Number', validators=[Length(max=50)])
    address = TextAreaField('Address', validators=[Length(max=250)])
    city = StringField('City', validators=[Length(max=100)])
    state = StringField('State/Province', validators=[Length(max=100)])
    country = StringField('Country', validators=[Length(max=100)])
    postal_code = StringField('Postal Code', validators=[Length(max=20)])
    website = StringField('Website', validators=[Length(max=200)])
    description = TextAreaField('Company Description', validators=[Length(max=500)])
    industry = SelectField('Industry', choices=[
        ('', 'Select Industry'),
        ('technology', 'Technology'),
        ('retail', 'Retail'),
        ('manufacturing', 'Manufacturing'),
        ('healthcare', 'Healthcare'),
        ('finance', 'Finance'),
        ('education', 'Education'),
        ('agriculture', 'Agriculture'),
        ('construction', 'Construction'),
        ('hospitality', 'Hospitality'),
        ('transportation', 'Transportation'),
        ('energy', 'Energy'),
        ('consulting', 'Consulting'),
        ('media', 'Media & Entertainment'),
        ('nonprofit', 'Non-Profit'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    # Founder Information
    founder_username = StringField('Founder Username', validators=[DataRequired(), Length(min=3, max=80)])
    founder_email = StringField('Founder Email', validators=[DataRequired(), Email(), Length(max=120)])
    founder_name = StringField('Founder Full Name', validators=[DataRequired(), Length(max=120)])
    founder_password = PasswordField('Founder Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), 
        EqualTo('founder_password', message='Passwords must match')
    ])
    
    submit = SubmitField('Register Company')
