class LoanRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(255))
    date_issued = db.Column(db.DateTime, default=datetime.utcnow)
    balance = db.Column(db.Float, nullable=False)
    monthly_installment = db.Column(db.Float, nullable=True)
    is_settled = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref='loan_records')
