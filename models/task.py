from datetime import datetime
from extensions import db

class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), default='Pending')  # Pending, Completed, Overdue
    priority = db.Column(db.String(50), default='Normal')  # Low, Normal, High
    related_to = db.Column(db.String(100), nullable=True)  # Lead, Contact, Deal (optional tag)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref='deals')