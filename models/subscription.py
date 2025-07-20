from datetime import datetime
from . import db
from sqlalchemy import Numeric

class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    plan_name = db.Column(db.String(100), nullable=False)
    plan_type = db.Column(db.String(50), nullable=False)  # 'monthly', 'annual', 'trial'
    status = db.Column(db.String(20), default='active')  # 'active', 'cancelled', 'expired', 'suspended'
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    price = db.Column(Numeric(10, 2), nullable=False)
    features = db.Column(db.JSON)  # Store plan features as JSON
    max_users = db.Column(db.Integer, default=5)
    max_storage_gb = db.Column(db.Integer, default=10)
    modules_limit = db.Column(db.Integer, default=3)  # Number of modules allowed
    active_modules = db.Column(db.Text)  # JSON string of active module names
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Subscription {self.plan_name} for company {self.company_id}>'

    def is_active(self):
        """Check if subscription is currently active"""
        return (self.status == 'active' and 
                self.start_date <= datetime.utcnow() <= self.end_date)

    def days_remaining(self):
        """Calculate days remaining in subscription"""
        if self.end_date and datetime.utcnow() < self.end_date:
            return (self.end_date - datetime.utcnow()).days
        return 0

    def is_expiring_soon(self, days=30):
        """Check if subscription expires within specified days"""
        return 0 < self.days_remaining() <= days

    def to_dict(self):
        """Convert subscription to dictionary for API responses"""
        return {
            'id': self.id,
            'company_id': self.company_id,
            'plan_name': self.plan_name,
            'plan_type': self.plan_type,
            'status': self.status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'price': float(self.price) if self.price else None,
            'features': self.features,
            'max_users': self.max_users,
            'max_storage_gb': self.max_storage_gb,
            'modules_limit': self.modules_limit,
            'active_modules': self.get_active_modules_list(),
            'is_active': self.is_active(),
            'days_remaining': self.days_remaining(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def get_active_modules_list(self):
        """Return list of active modules"""
        if self.active_modules:
            import json
            return json.loads(self.active_modules)
        return []
    
    def set_active_modules(self, modules_list):
        """Set active modules as JSON string"""
        import json
        self.active_modules = json.dumps(modules_list)
    
    def can_access_module(self, module_name):
        """Check if company can access a specific module"""
        active_modules = self.get_active_modules_list()
        return module_name in active_modules or len(active_modules) < self.modules_limit
    
    def add_module(self, module_name):
        """Add a module to active modules if under limit"""
        active_modules = self.get_active_modules_list()
        if module_name not in active_modules and len(active_modules) < self.modules_limit:
            active_modules.append(module_name)
            self.set_active_modules(active_modules)
            return True
        return False
    
    def remove_module(self, module_name):
        """Remove a module from active modules"""
        active_modules = self.get_active_modules_list()
        if module_name in active_modules:
            active_modules.remove(module_name)
            self.set_active_modules(active_modules)
            return True
        return False
