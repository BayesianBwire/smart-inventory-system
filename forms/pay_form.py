from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp, NumberRange

class STKPushForm(FlaskForm):
    phone = StringField("Phone Number", validators=[
        DataRequired(),
        Length(min=10, max=12, message="Phone number must be 10 to 12 digits"),
        Regexp(r'^(?:2547|07)\d{8}$', message="Phone must start with 07 or 2547 and contain 10 or 12 digits")
    ])
    amount = IntegerField("Amount (KES)", validators=[
        DataRequired(),
        NumberRange(min=1, message="Amount must be at least 1 KES")
    ])
    submit = SubmitField("Pay Now")
