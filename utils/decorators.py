from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def email_verified_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("⚠️ Please log in to access this page.", "warning")
            return redirect(url_for('login_page'))
        if not current_user.email_confirmed:
            flash("⚠️ Please verify your email to access this feature.", "warning")
            return redirect(url_for('unverified_notice'))  # We'll define this route
        return f(*args, **kwargs)
    return decorated_function
