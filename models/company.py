from . import db
import random
import string

class Company(db.Model):
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    unique_id = db.Column(db.String(6), nullable=False, unique=True)  # ABC12D format
    industry = db.Column(db.String(100), nullable=True)  # Added industry field
    address = db.Column(db.String(250))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120), unique=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

    # reverse relationship
    users = db.relationship("User", back_populates="company")

    @staticmethod
    def generate_unique_id():
        """Generate unique company ID in format: ABC12D (3 letters, 2 digits, 1 letter)"""
        while True:
            # Generate 3 random uppercase letters
            letters1 = ''.join(random.choices(string.ascii_uppercase, k=3))
            # Generate 2 random digits
            digits = ''.join(random.choices(string.digits, k=2))
            # Generate 1 random uppercase letter
            letter2 = random.choice(string.ascii_uppercase)
            
            # Combine to create unique ID
            unique_id = letters1 + digits + letter2
            
            # Check if this ID already exists
            existing = Company.query.filter_by(unique_id=unique_id).first()
            if not existing:
                return unique_id

    def __repr__(self):
        return f"<Company {self.name} ({self.unique_id})>"
