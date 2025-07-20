from . import db
from datetime import date

class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=True)
    national_id = db.Column(db.String(50), unique=True, nullable=False)
    joining_date = db.Column(db.Date, nullable=False)
    employment_status = db.Column(db.String(30), nullable=False, default='active')
    photo_filename = db.Column(db.String(255), nullable=True)

    # 👇 New ForeignKey to company
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    def __repr__(self):
        return f'<Employee {self.full_name} - {self.employee_id}>'
