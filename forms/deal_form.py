from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, TextAreaField, DateField, SubmitField
from wtforms.validators import DataRequired, Optional

class DealForm(FlaskForm):
    title = StringField("Deal Title", validators=[DataRequired()])
    value = FloatField("Deal Value (Ksh)", validators=[Optional()])
    stage = SelectField("Stage", choices=[
        ('Prospecting', 'Prospecting'),
        ('Proposal', 'Proposal'),
        ('Negotiation', 'Negotiation'),
        ('Closed Won', 'Closed Won'),
        ('Closed Lost', 'Closed Lost')
    ], validators=[Optional()])
    status = SelectField("Status", choices=[
        ('Open', 'Open'),
        ('Won', 'Won'),
        ('Lost', 'Lost')
    ], validators=[Optional()])
    contact_name = StringField("Contact Person", validators=[Optional()])
    expected_close_date = DateField("Expected Close Date", validators=[Optional()])
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Save Deal")
