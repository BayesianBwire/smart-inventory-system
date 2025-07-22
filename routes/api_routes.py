"""
Enterprise API Routes for RahaSoft ERP
Provides RESTful endpoints for third-party integrations
"""
from flask import request, jsonify, g, current_app
from flask_restful import Resource, reqparse
from datetime import datetime, timedelta
import csv
import io
from sqlalchemy import and_, or_

from models.api_framework import api, api_bp, BaseAPIResource, APIResponse, api_auth_required
from models.user import User
from models.company import Company
from models.product import Product
from models.crm import Customer
from models.product import Supplier
from models.finance import Invoice
from models.finance import Expense
from models.finance_extended import BankTransaction
from utils.cache_manager import cache, CacheConfig, APIResponseCache


# Authentication and Authorization
class APIAuthResource(BaseAPIResource):
    """API Authentication endpoints"""
    
    def post(self):
        """Generate API key"""
        parser = reqparse.RequestParser()
        parser.add_argument('username', required=True, help='Username is required')
        parser.add_argument('password', required=True, help='Password is required')
        parser.add_argument('key_name', required=True, help='API key name is required')
        parser.add_argument('permissions', type=list, default=['read'])
        parser.add_argument('expires_in_days', type=int, default=90)
        
        args = parser.parse_args()
        
        # Authenticate user
        user = User.query.filter_by(username=args['username']).first()
        if not user or not user.check_password(args['password']):
            return APIResponse.error(
                message="Invalid credentials",
                code="INVALID_CREDENTIALS",
                status_code=401
            )
        
        # Generate API key
        from models.api_framework import APIKey
        api_key, key_record = APIKey.generate_key(
            company_id=user.company_id,
            user_id=user.id,
            name=args['key_name'],
            permissions=args['permissions'],
            expires_in_days=args['expires_in_days']
        )
        
        return APIResponse.success({
            'api_key': api_key,
            'key_id': key_record.id,
            'expires_at': key_record.expires_at.isoformat(),
            'permissions': key_record.permissions
        }, message="API key generated successfully")


class APIKeyManagementResource(BaseAPIResource):
    """Manage API keys"""
    
    @api_auth_required(['admin'])
    def get(self):
        """List API keys for company"""
        from models.api_framework import APIKey
        
        keys = APIKey.query.filter_by(
            company_id=g.company.id,
            is_active=True
        ).all()
        
        return APIResponse.success([{
            'id': key.id,
            'name': key.name,
            'key_prefix': key.key_prefix + '...',
            'permissions': key.permissions,
            'total_requests': key.total_requests,
            'last_used': key.last_used.isoformat() if key.last_used else None,
            'created_at': key.created_at.isoformat(),
            'expires_at': key.expires_at.isoformat() if key.expires_at else None
        } for key in keys])
    
    @api_auth_required(['admin'])
    def delete(self, key_id):
        """Revoke API key"""
        from models.api_framework import APIKey
        
        api_key = APIKey.query.filter_by(
            id=key_id,
            company_id=g.company.id
        ).first()
        
        if not api_key:
            return APIResponse.error("API key not found", code="KEY_NOT_FOUND", status_code=404)
        
        api_key.revoke()
        return APIResponse.success(message="API key revoked successfully")


# Core Entity APIs
class CustomersAPIResource(BaseAPIResource):
    """Customer management API"""
    
    @api_auth_required(['read'])
    def get(self, customer_id=None):
        """Get customers or specific customer"""
        # Check cache first
        cache_key = f"customers:{g.company.id}:{customer_id or 'all'}"
        cached_data = APIResponseCache.get_api_response('customers', request.args, g.company.id)
        if cached_data:
            return cached_data
        
        if customer_id:
            customer = Customer.query.filter_by(
                id=customer_id,
                company_id=g.company.id
            ).first()
            
            if not customer:
                return APIResponse.error("Customer not found", code="CUSTOMER_NOT_FOUND", status_code=404)
            
            data = {
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone,
                'address': customer.address,
                'city': customer.city,
                'state': customer.state,
                'country': customer.country,
                'postal_code': customer.postal_code,
                'created_at': customer.created_at.isoformat(),
                'updated_at': customer.updated_at.isoformat() if customer.updated_at else None
            }
            
            response = APIResponse.success(data)
            APIResponseCache.set_api_response('customers', request.args, g.company.id, response)
            return response
        
        else:
            # List customers with pagination
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 50, type=int), 100)
            search = request.args.get('search', '')
            
            query = Customer.query.filter_by(company_id=g.company.id)
            
            if search:
                query = query.filter(or_(
                    Customer.name.ilike(f'%{search}%'),
                    Customer.email.ilike(f'%{search}%')
                ))
            
            customers = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            data = [{
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone,
                'city': customer.city,
                'country': customer.country
            } for customer in customers.items]
            
            response = APIResponse.paginated(
                data=data,
                page=page,
                per_page=per_page,
                total=customers.total
            )
            
            APIResponseCache.set_api_response('customers', request.args, g.company.id, response)
            return response
    
    @api_auth_required(['write'])
    def post(self):
        """Create new customer"""
        parser = reqparse.RequestParser()
        parser.add_argument('name', required=True, help='Customer name is required')
        parser.add_argument('email', required=True, help='Customer email is required')
        parser.add_argument('phone')
        parser.add_argument('address')
        parser.add_argument('city')
        parser.add_argument('state')
        parser.add_argument('country')
        parser.add_argument('postal_code')
        
        args = parser.parse_args()
        
        # Check if customer already exists
        existing = Customer.query.filter_by(
            email=args['email'],
            company_id=g.company.id
        ).first()
        
        if existing:
            return APIResponse.error(
                "Customer with this email already exists",
                code="CUSTOMER_EXISTS",
                status_code=409
            )
        
        # Create customer
        customer = Customer(
            company_id=g.company.id,
            name=args['name'],
            email=args['email'],
            phone=args.get('phone'),
            address=args.get('address'),
            city=args.get('city'),
            state=args.get('state'),
            country=args.get('country'),
            postal_code=args.get('postal_code')
        )
        
        from extensions import db
        db.session.add(customer)
        db.session.commit()
        
        # Invalidate cache
        from utils.cache_manager import CacheInvalidator
        CacheInvalidator.invalidate_company_cache(g.company.id)
        
        return APIResponse.success({
            'id': customer.id,
            'name': customer.name,
            'email': customer.email
        }, message="Customer created successfully", status_code=201)
    
    @api_auth_required(['write'])
    def put(self, customer_id):
        """Update customer"""
        customer = Customer.query.filter_by(
            id=customer_id,
            company_id=g.company.id
        ).first()
        
        if not customer:
            return APIResponse.error("Customer not found", code="CUSTOMER_NOT_FOUND", status_code=404)
        
        parser = reqparse.RequestParser()
        parser.add_argument('name')
        parser.add_argument('email')
        parser.add_argument('phone')
        parser.add_argument('address')
        parser.add_argument('city')
        parser.add_argument('state')
        parser.add_argument('country')
        parser.add_argument('postal_code')
        
        args = parser.parse_args()
        
        # Update fields
        for field, value in args.items():
            if value is not None:
                setattr(customer, field, value)
        
        customer.updated_at = datetime.utcnow()
        
        from extensions import db
        db.session.commit()
        
        # Invalidate cache
        from utils.cache_manager import CacheInvalidator
        CacheInvalidator.invalidate_company_cache(g.company.id)
        
        return APIResponse.success(message="Customer updated successfully")


class ProductsAPIResource(BaseAPIResource):
    """Product management API"""
    
    @api_auth_required(['read'])
    def get(self, product_id=None):
        """Get products or specific product"""
        # Check cache
        cached_data = APIResponseCache.get_api_response('products', request.args, g.company.id)
        if cached_data:
            return cached_data
        
        if product_id:
            product = Product.query.filter_by(
                id=product_id,
                company_id=g.company.id
            ).first()
            
            if not product:
                return APIResponse.error("Product not found", code="PRODUCT_NOT_FOUND", status_code=404)
            
            data = {
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'description': product.description,
                'category': product.category,
                'unit_price': float(product.unit_price) if product.unit_price else None,
                'cost_price': float(product.cost_price) if product.cost_price else None,
                'quantity_in_stock': product.quantity_in_stock,
                'reorder_level': product.reorder_level,
                'unit_of_measure': product.unit_of_measure,
                'is_active': product.is_active,
                'created_at': product.created_at.isoformat(),
                'updated_at': product.updated_at.isoformat() if product.updated_at else None
            }
            
            response = APIResponse.success(data)
            APIResponseCache.set_api_response('products', request.args, g.company.id, response)
            return response
        
        else:
            # List products with filtering
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 50, type=int), 100)
            search = request.args.get('search', '')
            category = request.args.get('category', '')
            low_stock = request.args.get('low_stock', 'false').lower() == 'true'
            
            query = Product.query.filter_by(company_id=g.company.id)
            
            if search:
                query = query.filter(or_(
                    Product.name.ilike(f'%{search}%'),
                    Product.sku.ilike(f'%{search}%')
                ))
            
            if category:
                query = query.filter(Product.category == category)
            
            if low_stock:
                query = query.filter(Product.quantity_in_stock <= Product.reorder_level)
            
            products = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            data = [{
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'category': product.category,
                'unit_price': float(product.unit_price) if product.unit_price else None,
                'quantity_in_stock': product.quantity_in_stock,
                'reorder_level': product.reorder_level,
                'is_active': product.is_active
            } for product in products.items]
            
            response = APIResponse.paginated(
                data=data,
                page=page,
                per_page=per_page,
                total=products.total
            )
            
            APIResponseCache.set_api_response('products', request.args, g.company.id, response)
            return response
    
    @api_auth_required(['write'])
    def post(self):
        """Create new product"""
        parser = reqparse.RequestParser()
        parser.add_argument('name', required=True, help='Product name is required')
        parser.add_argument('sku', required=True, help='Product SKU is required')
        parser.add_argument('description')
        parser.add_argument('category')
        parser.add_argument('unit_price', type=float)
        parser.add_argument('cost_price', type=float)
        parser.add_argument('quantity_in_stock', type=int, default=0)
        parser.add_argument('reorder_level', type=int, default=0)
        parser.add_argument('unit_of_measure', default='pcs')
        parser.add_argument('is_active', type=bool, default=True)
        
        args = parser.parse_args()
        
        # Check if SKU already exists
        existing = Product.query.filter_by(
            sku=args['sku'],
            company_id=g.company.id
        ).first()
        
        if existing:
            return APIResponse.error(
                "Product with this SKU already exists",
                code="PRODUCT_EXISTS",
                status_code=409
            )
        
        # Create product
        product = Product(
            company_id=g.company.id,
            **args
        )
        
        from extensions import db
        db.session.add(product)
        db.session.commit()
        
        # Invalidate cache
        from utils.cache_manager import CacheInvalidator
        CacheInvalidator.invalidate_company_cache(g.company.id)
        
        return APIResponse.success({
            'id': product.id,
            'name': product.name,
            'sku': product.sku
        }, message="Product created successfully", status_code=201)


class InvoicesAPIResource(BaseAPIResource):
    """Invoice management API"""
    
    @api_auth_required(['read'])
    def get(self, invoice_id=None):
        """Get invoices or specific invoice"""
        # Check cache
        cached_data = APIResponseCache.get_api_response('invoices', request.args, g.company.id)
        if cached_data:
            return cached_data
        
        if invoice_id:
            invoice = Invoice.query.filter_by(
                id=invoice_id,
                company_id=g.company.id
            ).first()
            
            if not invoice:
                return APIResponse.error("Invoice not found", code="INVOICE_NOT_FOUND", status_code=404)
            
            data = {
                'id': invoice.id,
                'invoice_number': invoice.invoice_number,
                'customer_id': invoice.customer_id,
                'customer_name': invoice.customer.name if invoice.customer else None,
                'issue_date': invoice.issue_date.isoformat(),
                'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
                'status': invoice.status,
                'subtotal': float(invoice.subtotal) if invoice.subtotal else None,
                'tax_amount': float(invoice.tax_amount) if invoice.tax_amount else None,
                'total_amount': float(invoice.total_amount) if invoice.total_amount else None,
                'paid_amount': float(invoice.paid_amount) if invoice.paid_amount else None,
                'created_at': invoice.created_at.isoformat(),
                'updated_at': invoice.updated_at.isoformat() if invoice.updated_at else None
            }
            
            response = APIResponse.success(data)
            APIResponseCache.set_api_response('invoices', request.args, g.company.id, response)
            return response
        
        else:
            # List invoices with filtering
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 50, type=int), 100)
            status = request.args.get('status', '')
            customer_id = request.args.get('customer_id', type=int)
            from_date = request.args.get('from_date')
            to_date = request.args.get('to_date')
            
            query = Invoice.query.filter_by(company_id=g.company.id)
            
            if status:
                query = query.filter(Invoice.status == status)
            
            if customer_id:
                query = query.filter(Invoice.customer_id == customer_id)
            
            if from_date:
                query = query.filter(Invoice.issue_date >= datetime.fromisoformat(from_date))
            
            if to_date:
                query = query.filter(Invoice.issue_date <= datetime.fromisoformat(to_date))
            
            invoices = query.order_by(Invoice.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            data = [{
                'id': invoice.id,
                'invoice_number': invoice.invoice_number,
                'customer_name': invoice.customer.name if invoice.customer else None,
                'issue_date': invoice.issue_date.isoformat(),
                'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
                'status': invoice.status,
                'total_amount': float(invoice.total_amount) if invoice.total_amount else None
            } for invoice in invoices.items]
            
            response = APIResponse.paginated(
                data=data,
                page=page,
                per_page=per_page,
                total=invoices.total
            )
            
            APIResponseCache.set_api_response('invoices', request.args, g.company.id, response)
            return response


# Analytics and Reporting APIs
class AnalyticsAPIResource(BaseAPIResource):
    """Analytics and reporting API"""
    
    @api_auth_required(['read'])
    def get(self, report_type):
        """Get analytics reports"""
        # Check cache
        cached_data = APIResponseCache.get_api_response(f'analytics/{report_type}', request.args, g.company.id)
        if cached_data:
            return cached_data
        
        if report_type == 'dashboard':
            data = self._get_dashboard_analytics()
        elif report_type == 'sales':
            data = self._get_sales_analytics()
        elif report_type == 'inventory':
            data = self._get_inventory_analytics()
        elif report_type == 'financial':
            data = self._get_financial_analytics()
        else:
            return APIResponse.error("Invalid report type", code="INVALID_REPORT_TYPE", status_code=400)
        
        response = APIResponse.success(data)
        APIResponseCache.set_api_response(f'analytics/{report_type}', request.args, g.company.id, response, ttl=CacheConfig.TTL_MEDIUM)
        return response
    
    def _get_dashboard_analytics(self):
        """Get dashboard analytics"""
        from sqlalchemy import func
        from extensions import db
        
        # Date range
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Revenue
        revenue = db.session.query(func.sum(Invoice.total_amount)).filter(
            Invoice.company_id == g.company.id,
            Invoice.status == 'paid',
            Invoice.created_at >= start_date
        ).scalar() or 0
        
        # Customer count
        customer_count = Customer.query.filter_by(company_id=g.company.id).count()
        
        # Product count
        product_count = Product.query.filter_by(company_id=g.company.id).count()
        
        # Pending invoices
        pending_invoices = Invoice.query.filter_by(
            company_id=g.company.id,
            status='pending'
        ).count()
        
        return {
            'revenue': float(revenue),
            'customer_count': customer_count,
            'product_count': product_count,
            'pending_invoices': pending_invoices,
            'period_days': days
        }
    
    def _get_sales_analytics(self):
        """Get sales analytics"""
        # Implementation for sales analytics
        return {'message': 'Sales analytics implementation pending'}
    
    def _get_inventory_analytics(self):
        """Get inventory analytics"""
        # Low stock products
        low_stock_products = Product.query.filter(
            Product.company_id == g.company.id,
            Product.quantity_in_stock <= Product.reorder_level
        ).count()
        
        # Total inventory value
        from sqlalchemy import func
        from extensions import db
        
        inventory_value = db.session.query(
            func.sum(Product.quantity_in_stock * Product.cost_price)
        ).filter(
            Product.company_id == g.company.id,
            Product.cost_price.isnot(None)
        ).scalar() or 0
        
        return {
            'low_stock_products': low_stock_products,
            'inventory_value': float(inventory_value)
        }
    
    def _get_financial_analytics(self):
        """Get financial analytics"""
        # Implementation for financial analytics
        return {'message': 'Financial analytics implementation pending'}


# Data Import/Export APIs
class DataImportAPIResource(BaseAPIResource):
    """Data import API"""
    
    @api_auth_required(['write'])
    def post(self, data_type):
        """Import data from CSV"""
        if data_type not in ['customers', 'products', 'invoices']:
            return APIResponse.error("Invalid data type", code="INVALID_DATA_TYPE", status_code=400)
        
        if 'file' not in request.files:
            return APIResponse.error("No file provided", code="NO_FILE", status_code=400)
        
        file = request.files['file']
        if not file.filename.endswith('.csv'):
            return APIResponse.error("Only CSV files are supported", code="INVALID_FILE_TYPE", status_code=400)
        
        try:
            # Process CSV file
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_input = csv.DictReader(stream)
            
            if data_type == 'customers':
                result = self._import_customers(csv_input)
            elif data_type == 'products':
                result = self._import_products(csv_input)
            elif data_type == 'invoices':
                result = self._import_invoices(csv_input)
            
            return APIResponse.success(result, message=f"{data_type.title()} imported successfully")
            
        except Exception as e:
            current_app.logger.error(f"Import error: {e}")
            return APIResponse.error("Import failed", code="IMPORT_ERROR", status_code=500)
    
    def _import_customers(self, csv_input):
        """Import customers from CSV"""
        imported = 0
        errors = []
        
        from extensions import db
        
        for row_num, row in enumerate(csv_input, start=2):
            try:
                # Check required fields
                if not row.get('name') or not row.get('email'):
                    errors.append(f"Row {row_num}: Name and email are required")
                    continue
                
                # Check if customer exists
                existing = Customer.query.filter_by(
                    email=row['email'],
                    company_id=g.company.id
                ).first()
                
                if existing:
                    errors.append(f"Row {row_num}: Customer with email {row['email']} already exists")
                    continue
                
                # Create customer
                customer = Customer(
                    company_id=g.company.id,
                    name=row['name'],
                    email=row['email'],
                    phone=row.get('phone'),
                    address=row.get('address'),
                    city=row.get('city'),
                    state=row.get('state'),
                    country=row.get('country'),
                    postal_code=row.get('postal_code')
                )
                
                db.session.add(customer)
                imported += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        db.session.commit()
        
        # Invalidate cache
        from utils.cache_manager import CacheInvalidator
        CacheInvalidator.invalidate_company_cache(g.company.id)
        
        return {
            'imported': imported,
            'errors': errors,
            'total_errors': len(errors)
        }
    
    def _import_products(self, csv_input):
        """Import products from CSV"""
        # Similar implementation for products
        return {'message': 'Product import implementation pending'}
    
    def _import_invoices(self, csv_input):
        """Import invoices from CSV"""
        # Similar implementation for invoices
        return {'message': 'Invoice import implementation pending'}


# Register API endpoints
api.add_resource(APIAuthResource, '/auth/token')
api.add_resource(APIKeyManagementResource, '/auth/keys', '/auth/keys/<int:key_id>')
api.add_resource(CustomersAPIResource, '/customers', '/customers/<int:customer_id>')
api.add_resource(ProductsAPIResource, '/products', '/products/<int:product_id>')
api.add_resource(InvoicesAPIResource, '/invoices', '/invoices/<int:invoice_id>')
api.add_resource(AnalyticsAPIResource, '/analytics/<string:report_type>')
api.add_resource(DataImportAPIResource, '/import/<string:data_type>')


# API Documentation endpoint
@api_bp.route('/docs')
def api_documentation():
    """API documentation"""
    return {
        'version': '1.0',
        'title': 'RahaSoft ERP API',
        'description': 'RESTful API for RahaSoft ERP system',
        'endpoints': {
            'authentication': {
                'POST /api/v1/auth/token': 'Generate API token',
                'GET /api/v1/auth/keys': 'List API keys',
                'DELETE /api/v1/auth/keys/{id}': 'Revoke API key'
            },
            'customers': {
                'GET /api/v1/customers': 'List customers',
                'POST /api/v1/customers': 'Create customer',
                'GET /api/v1/customers/{id}': 'Get customer',
                'PUT /api/v1/customers/{id}': 'Update customer'
            },
            'products': {
                'GET /api/v1/products': 'List products',
                'POST /api/v1/products': 'Create product',
                'GET /api/v1/products/{id}': 'Get product',
                'PUT /api/v1/products/{id}': 'Update product'
            },
            'invoices': {
                'GET /api/v1/invoices': 'List invoices',
                'GET /api/v1/invoices/{id}': 'Get invoice'
            },
            'analytics': {
                'GET /api/v1/analytics/dashboard': 'Dashboard analytics',
                'GET /api/v1/analytics/sales': 'Sales analytics',
                'GET /api/v1/analytics/inventory': 'Inventory analytics',
                'GET /api/v1/analytics/financial': 'Financial analytics'
            },
            'import': {
                'POST /api/v1/import/customers': 'Import customers from CSV',
                'POST /api/v1/import/products': 'Import products from CSV',
                'POST /api/v1/import/invoices': 'Import invoices from CSV'
            }
        },
        'authentication': {
            'type': 'Bearer Token',
            'header': 'Authorization: Bearer <api_key>',
            'description': 'Include API key in Authorization header'
        }
    }
