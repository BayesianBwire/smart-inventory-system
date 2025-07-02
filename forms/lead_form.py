from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Email

class LeadForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired()])
    email = StringField("Email", validators=[Optional(), Email()])
    phone = StringField("Phone", validators=[Optional()])
    company = StringField("Company", validators=[Optional()])
    lead_source = SelectField("Lead Source", choices=[
        ('', 'Select'), ('Referral', 'Referral'), ('Ads', 'Ads'), ('Cold Call', 'Cold Call'), ('Website', 'Website')
    ], validators=[Optional()])
    lead_status = SelectField("Lead Status", choices=[
        ('New', 'New'), ('Contacted', 'Contacted'), ('Qualified', 'Qualified'), ('Lost', 'Lost')
    ], validators=[Optional()])
    industry = StringField("Industry", validators=[Optional()])
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Save Lead")
