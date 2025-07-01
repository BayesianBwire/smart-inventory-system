from . import db

class Company(db.Model):
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    address = db.Column(db.String(250))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120), unique=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

    users = db.relationship("User", back_populates="company")
    employees = db.relationship("Employee", backref="company", lazy=True)  # 👈 Added line

    def __repr__(self):
        return f"<Company {self.name}>"
