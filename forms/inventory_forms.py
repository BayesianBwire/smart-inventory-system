from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, TextAreaField, SelectField, BooleanField, DateField, FileField
from wtforms.validators import DataRequired, NumberRange, Optional, Length, ValidationError
from models.product import Product, Category, Supplier
from flask_login import current_user

class ProductForm(FlaskForm):
    product_code = StringField('Product Code', validators=[DataRequired(), Length(min=1, max=100)])
    product_name = StringField('Product Name', validators=[DataRequired(), Length(min=1, max=255)])
    category = SelectField('Category', choices=[], validators=[Optional()])
    brand = StringField('Brand', validators=[Optional(), Length(max=100)])
    supplier = SelectField('Supplier', choices=[], validators=[Optional()])
    price = FloatField('Selling Price', validators=[DataRequired(), NumberRange(min=0)])
    cost_price = FloatField('Cost Price', validators=[Optional(), NumberRange(min=0)])
    quantity = IntegerField('Initial Quantity', validators=[DataRequired(), NumberRange(min=0)])
    reorder_level = IntegerField('Reorder Level', validators=[Optional(), NumberRange(min=0)], default=10)
    max_stock_level = IntegerField('Max Stock Level', validators=[Optional(), NumberRange(min=1)], default=1000)
    location = StringField('Storage Location', validators=[Optional(), Length(max=100)])
    barcode = StringField('Barcode', validators=[Optional(), Length(max=100)])
    weight = FloatField('Weight (kg)', validators=[Optional(), NumberRange(min=0)])
    dimensions = StringField('Dimensions (L x W x H)', validators=[Optional(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    tax_rate = FloatField('Tax Rate (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0)
    expiry_date = DateField('Expiry Date', validators=[Optional()])
    image = FileField('Product Image')
    is_active = BooleanField('Active', default=True)

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        if current_user.is_authenticated:
            # Populate category choices
            categories = Category.query.filter_by(
                company_id=current_user.company_id, 
                is_active=True
            ).all()
            self.category.choices = [('', 'Select Category')] + [(cat.name, cat.name) for cat in categories]
            
            # Populate supplier choices
            suppliers = Supplier.query.filter_by(
                company_id=current_user.company_id, 
                is_active=True
            ).all()
            self.supplier.choices = [('', 'Select Supplier')] + [(sup.name, sup.name) for sup in suppliers]

    def validate_product_code(self, field):
        if current_user.is_authenticated:
            existing_product = Product.query.filter_by(
                product_code=field.data,
                company_id=current_user.company_id
            ).first()
            if existing_product and (not hasattr(self, 'product_id') or existing_product.id != self.product_id):
                raise ValidationError('Product code already exists.')

    def validate_barcode(self, field):
        if field.data and current_user.is_authenticated:
            existing_product = Product.query.filter_by(
                barcode=field.data,
                company_id=current_user.company_id
            ).first()
            if existing_product and (not hasattr(self, 'product_id') or existing_product.id != self.product_id):
                raise ValidationError('Barcode already exists.')


class StockAdjustmentForm(FlaskForm):
    product_id = SelectField('Product', choices=[], validators=[DataRequired()])
    adjustment_type = SelectField('Adjustment Type', 
                                choices=[('add', 'Add Stock'), ('remove', 'Remove Stock'), ('set', 'Set Stock Level')],
                                validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    unit_cost = FloatField('Unit Cost', validators=[Optional(), NumberRange(min=0)])
    reference = StringField('Reference/PO Number', validators=[Optional(), Length(max=100)])
    notes = TextAreaField('Notes', validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super(StockAdjustmentForm, self).__init__(*args, **kwargs)
        if current_user.is_authenticated:
            products = Product.query.filter_by(
                company_id=current_user.company_id,
                is_active=True
            ).order_by(Product.product_name).all()
            self.product_id.choices = [(str(p.id), f"{p.product_code} - {p.product_name}") for p in products]


class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(min=1, max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    parent_id = SelectField('Parent Category', choices=[], validators=[Optional()])
    is_active = BooleanField('Active', default=True)

    def __init__(self, *args, **kwargs):
        super(CategoryForm, self).__init__(*args, **kwargs)
        if current_user.is_authenticated:
            categories = Category.query.filter_by(
                company_id=current_user.company_id,
                is_active=True
            ).all()
            self.parent_id.choices = [('', 'No Parent')] + [(str(cat.id), cat.name) for cat in categories]

    def validate_name(self, field):
        if current_user.is_authenticated:
            existing_category = Category.query.filter_by(
                name=field.data,
                company_id=current_user.company_id
            ).first()
            if existing_category and (not hasattr(self, 'category_id') or existing_category.id != self.category_id):
                raise ValidationError('Category name already exists.')


class SupplierForm(FlaskForm):
    name = StringField('Supplier Name', validators=[DataRequired(), Length(min=1, max=255)])
    contact_person = StringField('Contact Person', validators=[Optional(), Length(max=255)])
    email = StringField('Email', validators=[Optional(), Length(max=255)])
    phone = StringField('Phone', validators=[Optional(), Length(max=50)])
    address = TextAreaField('Address', validators=[Optional()])
    city = StringField('City', validators=[Optional(), Length(max=100)])
    state = StringField('State', validators=[Optional(), Length(max=100)])
    country = StringField('Country', validators=[Optional(), Length(max=100)])
    postal_code = StringField('Postal Code', validators=[Optional(), Length(max=20)])
    tax_id = StringField('Tax ID', validators=[Optional(), Length(max=50)])
    payment_terms = SelectField('Payment Terms', 
                               choices=[('', 'Select Terms'), ('Net 15', 'Net 15'), ('Net 30', 'Net 30'), 
                                       ('Net 60', 'Net 60'), ('Net 90', 'Net 90'), ('COD', 'Cash on Delivery')],
                               validators=[Optional()])
    credit_limit = FloatField('Credit Limit', validators=[Optional(), NumberRange(min=0)], default=0)
    rating = FloatField('Rating (1-5)', validators=[Optional(), NumberRange(min=1, max=5)])
    notes = TextAreaField('Notes', validators=[Optional()])
    is_active = BooleanField('Active', default=True)

    def validate_name(self, field):
        if current_user.is_authenticated:
            existing_supplier = Supplier.query.filter_by(
                name=field.data,
                company_id=current_user.company_id
            ).first()
            if existing_supplier and (not hasattr(self, 'supplier_id') or existing_supplier.id != self.supplier_id):
                raise ValidationError('Supplier name already exists.')


class BulkUploadForm(FlaskForm):
    csv_file = FileField('CSV File', validators=[DataRequired()])
    update_existing = BooleanField('Update Existing Products', default=False)

class InventorySearchForm(FlaskForm):
    search = StringField('Search Products')
    category = SelectField('Category', choices=[])
    stock_status = SelectField('Stock Status', 
                              choices=[('', 'All'), ('in_stock', 'In Stock'), ('low_stock', 'Low Stock'), 
                                      ('out_of_stock', 'Out of Stock'), ('overstocked', 'Overstocked')])
    price_min = FloatField('Min Price')
    price_max = FloatField('Max Price')

    def __init__(self, *args, **kwargs):
        super(InventorySearchForm, self).__init__(*args, **kwargs)
        if current_user.is_authenticated:
            categories = Category.query.filter_by(
                company_id=current_user.company_id,
                is_active=True
            ).all()
            self.category.choices = [('', 'All Categories')] + [(cat.name, cat.name) for cat in categories]
