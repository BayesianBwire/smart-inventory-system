from datetime import datetime
from models import db

class SupportTicket(db.Model):
    __tablename__ = 'support_tickets'

    id = db.Column(db.Integer, primary_key=True)
    submitted_by_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='Medium')
    category = db.Column(db.String(50), default='Technical')
    status = db.Column(db.String(20), default='Open')
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    submitted_by = db.relationship('Employee', foreign_keys=[submitted_by_id], backref='submitted_tickets')
    assigned_staff = db.relationship('Employee', foreign_keys=[assigned_staff_id], backref='assigned_tickets')
