from datetime import datetime
from . import db

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('bank_account.id'), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)  # +ve for deposit, -ve for withdrawal
    type = db.Column(db.String(20), nullable=False)  # 'deposit' or 'withdrawal'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(255))