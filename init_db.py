from app import app
from models.product import db

with app.app_context():
    db.create_all()
    print("✅ Tables created successfully.")
