from datetime import datetime
from extensions import db

class Communication(db.Model):
    __tablename__ = 'communications'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Message details
    message_type = db.Column(db.String(50), nullable=False)  # internal, whatsapp, email, sms
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    recipient_type = db.Column(db.String(20), nullable=False)  # user, customer, group, all
    recipient_id = db.Column(db.Integer, nullable=True)  # User ID if specific user
    
    # Content
    subject = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=False)
    attachment_urls = db.Column(db.JSON, nullable=True)
    
    # WhatsApp specific
    whatsapp_message_id = db.Column(db.String(200), nullable=True)
    whatsapp_phone = db.Column(db.String(20), nullable=True)
    whatsapp_status = db.Column(db.String(50), nullable=True)  # sent, delivered, read, failed
    
    # Email specific
    email_address = db.Column(db.String(200), nullable=True)
    email_message_id = db.Column(db.String(200), nullable=True)
    
    # Status and tracking
    status = db.Column(db.String(20), default='pending')  # pending, sent, delivered, failed
    delivery_time = db.Column(db.DateTime, nullable=True)
    read_time = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    # Priority and scheduling
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    scheduled_for = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='communications')
    sender = db.relationship('User', backref='sent_messages')
    
    def __repr__(self):
        return f"<Communication {self.message_type} - {self.subject or 'No Subject'}>"
    
    def mark_as_sent(self, delivery_time=None):
        """Mark message as sent"""
        self.status = 'sent'
        self.delivery_time = delivery_time or datetime.utcnow()
    
    def mark_as_delivered(self):
        """Mark message as delivered"""
        self.status = 'delivered'
        if not self.delivery_time:
            self.delivery_time = datetime.utcnow()
    
    def mark_as_read(self):
        """Mark message as read"""
        self.read_time = datetime.utcnow()
    
    def mark_as_failed(self, error_message):
        """Mark message as failed"""
        self.status = 'failed'
        self.error_message = error_message
    
    @classmethod
    def send_whatsapp_message(cls, company_id, sender_id, phone_number, message, subject=None):
        """Create a WhatsApp message record"""
        comm = cls(
            company_id=company_id,
            sender_id=sender_id,
            message_type='whatsapp',
            recipient_type='customer',
            whatsapp_phone=phone_number,
            subject=subject,
            message=message
        )
        db.session.add(comm)
        return comm
    
    @classmethod
    def send_internal_message(cls, company_id, sender_id, recipient_id, subject, message):
        """Create an internal message record"""
        comm = cls(
            company_id=company_id,
            sender_id=sender_id,
            message_type='internal',
            recipient_type='user',
            recipient_id=recipient_id,
            subject=subject,
            message=message
        )
        db.session.add(comm)
        return comm
    
    def to_dict(self):
        return {
            'id': self.id,
            'message_type': self.message_type,
            'subject': self.subject,
            'message': self.message,
            'status': self.status,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'delivery_time': self.delivery_time.isoformat() if self.delivery_time else None,
            'read_time': self.read_time.isoformat() if self.read_time else None
        }


class NotificationTemplate(db.Model):
    __tablename__ = 'notification_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)  # Null for system templates
    
    # Template details
    name = db.Column(db.String(100), nullable=False)
    template_type = db.Column(db.String(50), nullable=False)  # invoice, payment_reminder, welcome, etc.
    channel = db.Column(db.String(20), nullable=False)  # whatsapp, email, sms
    
    # Content
    subject_template = db.Column(db.String(200), nullable=True)
    message_template = db.Column(db.Text, nullable=False)
    
    # Settings
    is_active = db.Column(db.Boolean, default=True)
    is_system_template = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='notification_templates')
    
    def __repr__(self):
        return f"<NotificationTemplate {self.name} ({self.channel})>"
    
    def render(self, context_data):
        """Render template with context data"""
        try:
            from jinja2 import Template
            
            subject = None
            if self.subject_template:
                subject = Template(self.subject_template).render(**context_data)
            
            message = Template(self.message_template).render(**context_data)
            
            return {
                'subject': subject,
                'message': message
            }
        except Exception as e:
            return {
                'subject': self.subject_template,
                'message': f"Template error: {str(e)}"
            }
