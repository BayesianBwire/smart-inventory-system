from datetime import date
from . import db
from .employee import Employee

class Payroll(db.Model):
    __tablename__ = 'payrolls'

    id = db.Column(db.Integer, primary_key=True)

    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    employee = db.relationship('Employee', backref='payrolls')

    basic_salary = db.Column(db.Float, nullable=False)
    allowances = db.Column(db.Float, default=0.0)
    deductions = db.Column(db.Float, default=0.0)
    bonus = db.Column(db.Float, default=0.0)

    net_pay = db.Column(db.Float, nullable=False)

    month = db.Column(db.String(20), nullable=False)  # e.g., "July 2025"
    payment_date = db.Column(db.Date, default=date.today)

    payslip_filename = db.Column(db.String(255), nullable=True)
    remarks = db.Column(db.String(255), nullable=True)
