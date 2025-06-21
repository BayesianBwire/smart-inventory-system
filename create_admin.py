from flask import Flask
from models import db
from models.user import User
from werkzeug.security import generate_password_hash

# Step 1: Setup Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Step 2: Reset the admin user
with app.app_context():
    db.create_all()

    # Delete any existing admin user
    existing_admin = User.query.filter_by(username='admin').first()
    if existing_admin:
        db.session.delete(existing_admin)
        db.session.commit()
        print("🗑️ Old admin user deleted.")

    # Create new admin user with hashed password
    new_admin = User(
        username='admin',
        email='admin@example.com',
        password=generate_password_hash("admin")  # Correctly hashed
    )
    db.session.add(new_admin)
    db.session.commit()
    print("✅ New admin user created with username: admin and password: admin")
