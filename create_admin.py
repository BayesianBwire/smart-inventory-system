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

    print("\nAvailable roles:")
    print("1. superadmin\n2. admin\n3. sales_manager\n4. sales_attendant")
    print("5. inventory_manager\n6. hr_manager\n7. accountant\n8. viewer\n")

    username = input("Enter username: ").strip()
    email = input("Enter email: ").strip().lower()
    password = input("Enter password: ").strip()
    role = input("Enter role: ").strip().lower()

    allowed_roles = [
        'superadmin', 'admin', 'sales_manager', 'sales_attendant',
        'inventory_manager', 'hr_manager', 'accountant', 'viewer'
    ]

    if role not in allowed_roles:
        print("❌ Invalid role. Please use one of the predefined roles.")
    else:
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
            print(f"✅ User '{username}' with role '{role}' created successfully!")
        else:
            print("⚠️ User already exists.")
