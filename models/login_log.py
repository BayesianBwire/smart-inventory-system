from datetime import datetime
from models import db

class LoginLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    username = db.Column(db.String(80), nullable=False)
    ip_address = db.Column(db.String(100))
    browser_info = db.Column(db.String(255))  # ✅ This line was missing
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<LoginLog {self.username} - {self.timestamp}>"
