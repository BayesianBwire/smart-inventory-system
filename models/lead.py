from datetime import datetime
from extensions import db

class Lead(db.Model):
    __tablename__ = 'leads'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    company = db.Column(db.String(100), nullable=True)
    lead_source = db.Column(db.String(50), nullable=True)  # e.g., Referral, Ads
    lead_status = db.Column(db.String(50), nullable=True)  # e.g., New, Contacted
    industry = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref='leads')