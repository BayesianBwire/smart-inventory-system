# filepath: c:\Users\bilfo\smartshop\models\bank_account.py
from models import db

class BankAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    bank_name = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(50))
    account_type = db.Column(db.String(50))
    currency = db.Column(db.String(10))
    opening_balance = db.Column(db.Float, default=0.0)
    chart_of_accounts = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    current_balance = db.Column(db.Float, default=0.0)
    transactions = db.relationship('Transaction', backref='account', lazy=True)