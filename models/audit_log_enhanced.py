from datetime import datetime
from extensions import db

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    
    # Action details
    action = db.Column(db.String(100), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT
    resource_type = db.Column(db.String(50), nullable=False)  # User, Product, Sale, etc.
    resource_id = db.Column(db.Integer, nullable=True)
    
    # Request details
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    request_url = db.Column(db.String(500), nullable=True)
    request_method = db.Column(db.String(10), nullable=True)
    
    # Change details
    old_values = db.Column(db.JSON, nullable=True)
    new_values = db.Column(db.JSON, nullable=True)
    
    # Additional context
    description = db.Column(db.Text, nullable=True)
    severity = db.Column(db.String(20), default='INFO')  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='audit_logs')
    company = db.relationship('Company', backref='audit_logs')
    
    def __repr__(self):
        return f"<AuditLog {self.action} on {self.resource_type} by User {self.user_id}>"
    
    @classmethod
    def log_action(cls, user_id, action, resource_type, resource_id=None, 
                   old_values=None, new_values=None, description=None, 
                   ip_address=None, user_agent=None, company_id=None):
        """Helper method to create audit log entries"""
        log = cls(
            user_id=user_id,
            company_id=company_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(log)
        return log
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'company_id': self.company_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'description': self.description,
            'severity': self.severity,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
