# forms/product_form.py

from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, IntegerField, SubmitField
from wtforms.validators import DataRequired

class ProductForm(FlaskForm):
    name = StringField("Product Name", validators=[DataRequired()])
    price = DecimalField("Price", validators=[DataRequired()])
    quantity = IntegerField("Quantity", validators=[DataRequired()])
    submit = SubmitField("Save")
