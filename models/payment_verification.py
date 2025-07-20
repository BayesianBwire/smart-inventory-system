from datetime import datetime
from extensions import db

class PaymentVerification(db.Model):
    __tablename__ = 'payment_verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Payment details
    payment_method = db.Column(db.String(50), nullable=False)  # mpesa, paypal, bank
    transaction_id = db.Column(db.String(200), nullable=False, unique=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), default='KES')
    
    # M-Pesa specific
    mpesa_receipt_number = db.Column(db.String(100), nullable=True)
    mpesa_phone_number = db.Column(db.String(20), nullable=True)
    mpesa_transaction_date = db.Column(db.DateTime, nullable=True)
    
    # PayPal specific
    paypal_payment_id = db.Column(db.String(200), nullable=True)
    paypal_payer_id = db.Column(db.String(200), nullable=True)
    
    # Bank transfer specific
    bank_reference = db.Column(db.String(200), nullable=True)
    bank_account_number = db.Column(db.String(50), nullable=True)
    
    # Verification status
    status = db.Column(db.String(20), default='pending')  # pending, verified, failed, cancelled
    verification_method = db.Column(db.String(50), nullable=True)  # api, manual, webhook
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)
    
    # Additional data
    webhook_data = db.Column(db.JSON, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    failure_reason = db.Column(db.String(500), nullable=True)
    
    # Purpose of payment
    purpose = db.Column(db.String(100), nullable=True)  # subscription, invoice, product, etc.
    reference_id = db.Column(db.Integer, nullable=True)  # Related record ID
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='payments')
    user = db.relationship('User', foreign_keys=[user_id], backref='payment_transactions')
    verifier = db.relationship('User', foreign_keys=[verified_by])
    
    def __repr__(self):
        return f"<Payment {self.transaction_id} - {self.amount} {self.currency} ({self.status})>"
    
    def verify_payment(self, verifier_id, notes=None):
        """Mark payment as verified"""
        self.status = 'verified'
        self.verified_by = verifier_id
        self.verified_at = datetime.utcnow()
        if notes:
            self.notes = notes
    
    def fail_payment(self, reason):
        """Mark payment as failed"""
        self.status = 'failed'
        self.failure_reason = reason
    
    def is_verified(self):
        return self.status == 'verified'
    
    def is_pending(self):
        return self.status == 'pending'
    
    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'amount': float(self.amount),
            'currency': self.currency,
            'payment_method': self.payment_method,
            'status': self.status,
            'purpose': self.purpose,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None
        }
