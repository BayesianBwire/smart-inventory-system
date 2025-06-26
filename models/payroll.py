from datetime import datetime
from models import db

class PayrollRecord(db.Model):
    __tablename__ = 'payroll_record'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.String(20), nullable=False)
    loan_deduction = db.Column(db.Float, default=0)
    remarks = db.Column(db.String(255))
    
    date = db.Column(db.DateTime, default=datetime.utcnow)  # ✅ This line is missing in your model

    user = db.relationship('User', backref='payroll_records')
