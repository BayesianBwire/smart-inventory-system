from flask import Flask
from models import db
from models.user import User
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

    username = input("Enter username: ")
    email = input("Enter email: ")
    password = input("Enter password: ")
    role = input("Enter role (admin/attendant/manager): ")

    existing_user = User.query.filter_by(username=username).first()
    if not existing_user:
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=role
        )
        db.session.add(user)
        db.session.commit()
        print("✅ User created successfully!")
    else:
        print("⚠️ User already exists.")
