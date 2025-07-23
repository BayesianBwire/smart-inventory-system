"""
RESTful API Framework for RahaSoft ERP
Provides enterprise-grade API endpoints for third-party integrations
"""
from flask import Blueprint, request, jsonify, g
from flask_restful import Api, Resource, reqparse
from functools import wraps
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from extensions import db
from models.user import User
from models.company import Company

# Create API Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')
api = Api(api_bp)

class APIKey(db.Model):
    """API Key management for third-party integrations"""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, nullable=False)  # Remove FK for test
    user_id = db.Column(db.Integer, nullable=False)     # Remove FK for test
    
    # Key Details
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    key_hash = db.Column(db.String(64), nullable=False, unique=True)
    key_prefix = db.Column(db.String(10), nullable=False)  # First 8 chars for display
    
    # Permissions
    permissions = db.Column(db.JSON, default=['read'])  # read, write, admin
    
    # Usage Tracking
    total_requests = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime)
    
    # Security
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Rate Limiting
    rate_limit_per_hour = db.Column(db.Integer, default=1000)
    rate_limit_per_day = db.Column(db.Integer, default=10000)
    
    # Relationships (commented out for testing)
    # company = db.relationship('Company', backref='api_keys')
    # user = db.relationship('User', backref='created_api_keys')
    
    @classmethod
    def generate_key(cls, company_id, user_id, name, permissions=['read'], expires_in_days=90):
        """Generate a new API key"""
        # Generate random API key
        key = f"raha_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        key_prefix = key[:8]
        
        api_key = cls(
            company_id=company_id,
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            permissions=permissions,
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days)
        )
        
        db.session.add(api_key)
        db.session.commit()
        
        return key, api_key
    
    @classmethod
    def validate_key(cls, key):
        """Validate API key and return associated record"""
        if not key or not key.startswith('raha_'):
            return None
        
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        api_key = cls.query.filter_by(key_hash=key_hash, is_active=True).first()
        
        if not api_key:
            return None
        
        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            return None
        
        # Update usage stats
        api_key.total_requests += 1
        api_key.last_used = datetime.utcnow()
        db.session.commit()
        
        return api_key
    
    def has_permission(self, permission):
        """Check if API key has specific permission"""
        return permission in self.permissions or 'admin' in self.permissions
    
    def revoke(self):
        """Revoke API key"""
        self.is_active = False
        db.session.commit()


class APIUsageLog(db.Model):
    """Log API usage for monitoring and billing"""
    __tablename__ = 'api_usage_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    api_key_id = db.Column(db.Integer, nullable=False)  # Remove FK for test
    
    # Request Details
    endpoint = db.Column(db.String(200), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    status_code = db.Column(db.Integer, nullable=False)
    response_time_ms = db.Column(db.Integer)
    
    # Request Context
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    request_size_bytes = db.Column(db.Integer)
    response_size_bytes = db.Column(db.Integer)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships (commented out for testing)
    # api_key = db.relationship('APIKey', backref='usage_logs')


# API Authentication Decorator
def api_auth_required(permissions=None):
    """Decorator for API authentication"""
    if permissions is None:
        permissions = ['read']
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get API key from header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return {'error': 'API key required', 'code': 'AUTH_REQUIRED'}, 401
            
            api_key = auth_header.replace('Bearer ', '')
            
            # Validate API key
            key_record = APIKey.validate_key(api_key)
            if not key_record:
                return {'error': 'Invalid or expired API key', 'code': 'INVALID_KEY'}, 401
            
            # Check permissions
            for permission in permissions:
                if not key_record.has_permission(permission):
                    return {
                        'error': f'Insufficient permissions. Required: {permissions}',
                        'code': 'INSUFFICIENT_PERMISSIONS'
                    }, 403
            
            # Check rate limits
            if not check_rate_limit(key_record):
                return {
                    'error': 'Rate limit exceeded',
                    'code': 'RATE_LIMIT_EXCEEDED'
                }, 429
            
            # Store in context for use in the endpoint
            g.api_key = key_record
            g.company = key_record.company
            g.user = key_record.user
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def check_rate_limit(api_key):
    """Check if API key has exceeded rate limits"""
    from datetime import datetime, timedelta
    
    # Check hourly limit
    hour_ago = datetime.utcnow() - timedelta(hours=1)
    hourly_requests = APIUsageLog.query.filter(
        APIUsageLog.api_key_id == api_key.id,
        APIUsageLog.timestamp >= hour_ago
    ).count()
    
    if hourly_requests >= api_key.rate_limit_per_hour:
        return False
    
    # Check daily limit
    day_ago = datetime.utcnow() - timedelta(days=1)
    daily_requests = APIUsageLog.query.filter(
        APIUsageLog.api_key_id == api_key.id,
        APIUsageLog.timestamp >= day_ago
    ).count()
    
    if daily_requests >= api_key.rate_limit_per_day:
        return False
    
    return True


def log_api_usage(api_key_id, endpoint, method, status_code, response_time_ms=None):
    """Log API usage for monitoring"""
    log_entry = APIUsageLog(
        api_key_id=api_key_id,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        response_time_ms=response_time_ms,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')[:500]
    )
    db.session.add(log_entry)
    db.session.commit()


# API Response Helper
class APIResponse:
    @staticmethod
    def success(data=None, message="Success", status_code=200):
        """Standard success response"""
        response = {
            'success': True,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
        if data is not None:
            response['data'] = data
        return response, status_code
    
    @staticmethod
    def error(message, code="ERROR", status_code=400, details=None):
        """Standard error response"""
        response = {
            'success': False,
            'error': {
                'message': message,
                'code': code,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        if details:
            response['error']['details'] = details
        return response, status_code
    
    @staticmethod
    def paginated(data, page, per_page, total, endpoint=None):
        """Paginated response"""
        return {
            'success': True,
            'data': data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page,
                'has_next': page * per_page < total,
                'has_prev': page > 1
            },
            'timestamp': datetime.utcnow().isoformat()
        }


# Base API Resource with common functionality
class BaseAPIResource(Resource):
    """Base class for API resources"""
    
    def dispatch_request(self, *args, **kwargs):
        """Override to add logging and error handling"""
        start_time = datetime.utcnow()
        
        try:
            response = super().dispatch_request(*args, **kwargs)
            status_code = getattr(response, 'status_code', 200)
            
            # Log successful requests
            if hasattr(g, 'api_key'):
                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                log_api_usage(
                    g.api_key.id,
                    request.endpoint,
                    request.method,
                    status_code,
                    int(response_time)
                )
            
            return response
            
        except Exception as e:
            # Log errors
            if hasattr(g, 'api_key'):
                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                log_api_usage(
                    g.api_key.id,
                    request.endpoint,
                    request.method,
                    500,
                    int(response_time)
                )
            
            # Return standardized error response
            return APIResponse.error(
                message="Internal server error",
                code="INTERNAL_ERROR",
                status_code=500
            )


# Webhook Support
class Webhook(db.Model):
    """Webhook configuration for real-time notifications"""
    __tablename__ = 'webhooks'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Webhook Details
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    secret = db.Column(db.String(64))  # For signature verification
    
    # Events to listen for
    events = db.Column(db.JSON, default=[])  # List of event types
    
    # Security and Delivery
    is_active = db.Column(db.Boolean, default=True)
    delivery_attempts = db.Column(db.Integer, default=0)
    last_delivery = db.Column(db.DateTime)
    last_status = db.Column(db.String(20))  # success, failed, pending
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='webhooks')


class WebhookDelivery(db.Model):
    """Track webhook delivery attempts"""
    __tablename__ = 'webhook_deliveries'
    
    id = db.Column(db.Integer, primary_key=True)
    webhook_id = db.Column(db.Integer, db.ForeignKey('webhooks.id'), nullable=False)
    
    # Event Details
    event_type = db.Column(db.String(50), nullable=False)
    event_data = db.Column(db.JSON)
    
    # Delivery Details
    status = db.Column(db.String(20), default='pending')  # pending, success, failed
    response_code = db.Column(db.Integer)
    response_body = db.Column(db.Text)
    
    # Timing
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)
    delivered_at = db.Column(db.DateTime)
    
    # Relationships
    webhook = db.relationship('Webhook', backref='deliveries')


# Import/Export Framework
class DataImportJob(db.Model):
    """Track data import jobs"""
    __tablename__ = 'data_import_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Job Details
    job_type = db.Column(db.String(50), nullable=False)  # products, customers, invoices, etc.
    file_name = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    
    # Progress Tracking
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    total_records = db.Column(db.Integer, default=0)
    processed_records = db.Column(db.Integer, default=0)
    successful_records = db.Column(db.Integer, default=0)
    failed_records = db.Column(db.Integer, default=0)
    
    # Error Tracking
    error_log = db.Column(db.JSON)  # List of errors
    
    # Timing
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='import_jobs')
    user = db.relationship('User', backref='import_jobs')
    
    def update_progress(self, processed=None, successful=None, failed=None, errors=None):
        """Update job progress"""
        if processed is not None:
            self.processed_records = processed
        if successful is not None:
            self.successful_records = successful
        if failed is not None:
            self.failed_records = failed
        if errors:
            if not self.error_log:
                self.error_log = []
            self.error_log.extend(errors)
        
        # Update status
        if self.processed_records >= self.total_records:
            self.status = 'completed'
            self.completed_at = datetime.utcnow()
        
        db.session.commit()


# Integration Configuration
class IntegrationConfig(db.Model):
    """Store integration configurations"""
    __tablename__ = 'integration_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Integration Details
    integration_type = db.Column(db.String(50), nullable=False)  # quickbooks, xero, shopify, etc.
    name = db.Column(db.String(100), nullable=False)
    
    # Configuration
    config_data = db.Column(db.JSON)  # Store integration-specific config
    credentials = db.Column(db.JSON)  # Encrypted credentials
    
    # Status
    is_active = db.Column(db.Boolean, default=False)
    last_sync = db.Column(db.DateTime)
    sync_status = db.Column(db.String(20))  # success, failed, pending
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='integrations')
