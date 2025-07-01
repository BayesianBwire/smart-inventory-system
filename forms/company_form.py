from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length

class CompanyForm(FlaskForm):
    name = StringField('Company Name', validators=[DataRequired(), Length(max=150)])
    address = StringField('Address', validators=[Length(max=250)])
    phone = StringField('Phone', validators=[Length(max=50)])
    submit = SubmitField('Register Company')
