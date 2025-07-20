from datetime import datetime, timedelta
from extensions import db
from sqlalchemy import func

class BusinessMetrics(db.Model):
    __tablename__ = 'business_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Date for metrics
    date = db.Column(db.Date, nullable=False)
    
    # Sales metrics
    daily_revenue = db.Column(db.Numeric(12, 2), default=0)
    daily_sales_count = db.Column(db.Integer, default=0)
    daily_customers = db.Column(db.Integer, default=0)
    average_order_value = db.Column(db.Numeric(10, 2), default=0)
    
    # Inventory metrics
    products_sold = db.Column(db.Integer, default=0)
    low_stock_alerts = db.Column(db.Integer, default=0)
    inventory_value = db.Column(db.Numeric(12, 2), default=0)
    
    # User activity metrics
    active_users = db.Column(db.Integer, default=0)
    login_count = db.Column(db.Integer, default=0)
    
    # Financial metrics
    expenses = db.Column(db.Numeric(12, 2), default=0)
    profit_margin = db.Column(db.Numeric(5, 2), default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='metrics')
    
    __table_args__ = (db.UniqueConstraint('company_id', 'date'),)
    
    def __repr__(self):
        return f"<BusinessMetrics {self.company_id} - {self.date}>"
    
    @classmethod
    def get_or_create_today(cls, company_id):
        """Get or create today's metrics record"""
        today = datetime.utcnow().date()
        metrics = cls.query.filter_by(company_id=company_id, date=today).first()
        if not metrics:
            metrics = cls(company_id=company_id, date=today)
            db.session.add(metrics)
        return metrics
    
    @classmethod
    def calculate_business_health_score(cls, company_id, days=30):
        """Calculate overall business health score (0-100)"""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        metrics = cls.query.filter(
            cls.company_id == company_id,
            cls.date >= start_date,
            cls.date <= end_date
        ).all()
        
        if not metrics:
            return 0
        
        # Calculate various health indicators
        revenue_trend = sum(m.daily_revenue for m in metrics[-7:]) / 7 if len(metrics) >= 7 else 0
        profit_avg = sum(m.profit_margin for m in metrics) / len(metrics)
        activity_score = sum(m.active_users for m in metrics) / len(metrics)
        
        # Simple health score calculation (can be enhanced)
        health_score = min(100, 
            (float(revenue_trend) / 1000 * 20) +  # Revenue component (up to 20 points)
            (float(profit_avg) * 2) +             # Profit margin component (up to 40 points)
            (activity_score * 2)                  # User activity component (up to 40 points)
        )
        
        return max(0, min(100, health_score))
    
    def to_dict(self):
        return {
            'date': self.date.isoformat(),
            'daily_revenue': float(self.daily_revenue),
            'daily_sales_count': self.daily_sales_count,
            'daily_customers': self.daily_customers,
            'average_order_value': float(self.average_order_value),
            'products_sold': self.products_sold,
            'low_stock_alerts': self.low_stock_alerts,
            'inventory_value': float(self.inventory_value),
            'active_users': self.active_users,
            'profit_margin': float(self.profit_margin)
        }


class AIInsights(db.Model):
    __tablename__ = 'ai_insights'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Insight details
    insight_type = db.Column(db.String(50), nullable=False)  # sales_prediction, inventory_alert, etc.
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default='INFO')  # INFO, WARNING, CRITICAL
    
    # AI confidence and data
    confidence_score = db.Column(db.Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    recommendation = db.Column(db.Text, nullable=True)
    data_source = db.Column(db.JSON, nullable=True)
    
    # Status
    status = db.Column(db.String(20), default='active')  # active, dismissed, resolved
    dismissed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    dismissed_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    company = db.relationship('Company', backref='ai_insights')
    dismisser = db.relationship('User')
    
    def __repr__(self):
        return f"<AIInsight {self.insight_type} - {self.title}>"
    
    def dismiss(self, user_id):
        """Dismiss this insight"""
        self.status = 'dismissed'
        self.dismissed_by = user_id
        self.dismissed_at = datetime.utcnow()
    
    def is_active(self):
        return (self.status == 'active' and 
                (not self.expires_at or self.expires_at > datetime.utcnow()))
    
    @classmethod
    def create_insight(cls, company_id, insight_type, title, description, 
                      severity='INFO', confidence_score=None, recommendation=None,
                      expires_hours=72):
        """Create a new AI insight"""
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours) if expires_hours else None
        
        insight = cls(
            company_id=company_id,
            insight_type=insight_type,
            title=title,
            description=description,
            severity=severity,
            confidence_score=confidence_score,
            recommendation=recommendation,
            expires_at=expires_at
        )
        db.session.add(insight)
        return insight
