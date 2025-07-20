from flask import Blueprint, render_template, redirect, url_for, flash, request
from models import db, User
from forms.user_form import UserForm
from werkzeug.security import generate_password_hash
from flask_login import login_required

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/users', methods=['GET'])
@login_required
def list_users():
    users = User.query.all()
    return render_template('users/list.html', users=users)

@user_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
def create_user():
    form = UserForm()
    if form.validate_on_submit():
        new_user = User(
            full_name=form.full_name.data,
            username=form.username.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
            password=form.password.data,
            role=form.role.data,
            email_confirmed=True  # You can change this logic later
        )
        db.session.add(new_user)
        db.session.commit()
        flash("✅ New user created successfully!", "success")
        return redirect(url_for('user_bp.list_users'))
    return render_template('users/create.html', form=form)
