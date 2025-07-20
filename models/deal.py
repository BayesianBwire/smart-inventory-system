from datetime import datetime
from extensions import db

class Deal(db.Model):
    __tablename__ = 'deals'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    value = db.Column(db.Float, nullable=True)
    stage = db.Column(db.String(50), nullable=True)  # e.g., Prospecting, Negotiation
    status = db.Column(db.String(50), nullable=True)  # e.g., Open, Won, Lost
    contact_name = db.Column(db.String(100), nullable=True)
    expected_close_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
