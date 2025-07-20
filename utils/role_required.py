# utils/role_required.py

from functools import wraps
from flask_login import current_user
from flask import abort

def role_required(role):
    def wrapper(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                return abort(403)  # Forbidden
            return func(*args, **kwargs)
        return decorated_view
    return wrapper
