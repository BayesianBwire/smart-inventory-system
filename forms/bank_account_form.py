from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField
from wtforms.validators import DataRequired, Length

class BankAccountForm(FlaskForm):
    account_name = StringField('Account Name', validators=[DataRequired(), Length(max=120)])
    account_number = StringField('Account Number', validators=[DataRequired(), Length(max=50)])
    bank_name = StringField('Bank Name', validators=[DataRequired(), Length(max=120)])
    balance = FloatField('Initial Balance')
    submit = SubmitField('Save')
