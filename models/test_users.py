from app import app
from models.user import User

with app.app_context():
    users = User.query.all()
    for u in users:
        print(u.email)
