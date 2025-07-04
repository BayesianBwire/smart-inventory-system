from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, AttendanceRecord, Employee  # make sure model is imported

attendance_bp = Blueprint('attendance_bp', __name__)

@attendance_bp.route('/hr/attendance', methods=['GET', 'POST'])
def attendance_list():
    employees = Employee.query.all()
    records = AttendanceRecord.query.order_by(AttendanceRecord.date.desc()).all()
    return render_template('hr/attendance.html', employees=employees, records=records)
