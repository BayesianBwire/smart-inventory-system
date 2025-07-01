from . import db  # ✅ This imports the db object defined in models/__init__.py
from datetime import datetime
from sqlalchemy import Enum

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    check_in_time = db.Column(db.Time)
    check_out_time = db.Column(db.Time)
    status = db.Column(db.Enum('Present', 'Absent', 'Leave', 'Late', name='attendance_status'), nullable=False)

    employee = db.relationship('Employee', backref='attendance_records')
