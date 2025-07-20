from datetime import datetime, timedelta
from extensions import db
from sqlalchemy import func
import json

class PayrollAutomation(db.Model):
    """Auto Payroll Split to Employee Bank/M-Pesa Accounts"""
    __tablename__ = 'payroll_automation'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    payroll_id = db.Column(db.Integer, db.ForeignKey('payrolls.id'), nullable=False)
    
    # Payment schedule
    payment_date = db.Column(db.Date, nullable=False)
    frequency = db.Column(db.String(20), default='monthly')  # weekly, bi-weekly, monthly
    
    # Automation settings
    auto_send_enabled = db.Column(db.Boolean, default=False)
    require_approval = db.Column(db.Boolean, default=True)
    
    # Split configuration
    payment_splits = db.Column(db.JSON, nullable=False)  # How to split payments across methods
    
    # Status tracking
    status = db.Column(db.String(20), default='pending')  # pending, approved, processing, completed, failed
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Processing results
    successful_payments = db.Column(db.Integer, default=0)
    failed_payments = db.Column(db.Integer, default=0)
    processing_details = db.Column(db.JSON, nullable=True)
    
    # Approval
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    company = db.relationship('Company', backref='payroll_automation')
    payroll = db.relationship('Payroll', backref='automation_records')
    approver = db.relationship('User', backref='approved_payrolls')
    
    def process_payments(self):
        """Process automated payments to employees"""
        if self.status != 'approved':
            return False, "Payroll not approved for processing"
        
        self.status = 'processing'
        self.processed_at = datetime.utcnow()
        
        # Process each payment split (would integrate with M-Pesa/Bank APIs)
        results = []
        for split in self.payment_splits:
            employee_id = split.get('employee_id')
            amount = split.get('amount')
            method = split.get('method')  # mpesa, bank, cash
            
            # Simulate payment processing
            success = self._send_payment(employee_id, amount, method)
            results.append({
                'employee_id': employee_id,
                'amount': amount,
                'method': method,
                'success': success,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            if success:
                self.successful_payments += 1
            else:
                self.failed_payments += 1
        
        self.processing_details = results
        self.status = 'completed' if self.failed_payments == 0 else 'partial_success'
        
        return True, f"Processed {self.successful_payments} successful payments"
    
    def _send_payment(self, employee_id, amount, method):
        """Send payment via specified method"""
        # In production, this would integrate with actual payment APIs
        # For now, we'll simulate success/failure
        return True  # Simulated success


class PriceRecommendation(db.Model):
    """Smart Price Recommendation Engine"""
    __tablename__ = 'price_recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    # Current pricing
    current_price = db.Column(db.Numeric(10, 2), nullable=False)
    cost_price = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Recommended pricing
    recommended_price = db.Column(db.Numeric(10, 2), nullable=False)
    min_price = db.Column(db.Numeric(10, 2), nullable=False)
    max_price = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Analysis factors
    sales_velocity = db.Column(db.Float, default=0.0)  # Units sold per day
    profit_margin_current = db.Column(db.Float, default=0.0)
    profit_margin_recommended = db.Column(db.Float, default=0.0)
    
    # Market analysis
    competitor_avg_price = db.Column(db.Numeric(10, 2), nullable=True)
    market_demand_score = db.Column(db.Float, default=0.5)  # 0.0 to 1.0
    seasonality_factor = db.Column(db.Float, default=1.0)
    
    # AI confidence and reasoning
    confidence_score = db.Column(db.Float, default=0.0)  # 0.0 to 1.0
    recommendation_reason = db.Column(db.Text, nullable=True)
    
    # Implementation tracking
    implemented = db.Column(db.Boolean, default=False)
    implemented_at = db.Column(db.DateTime, nullable=True)
    
    # Results tracking
    sales_before = db.Column(db.Integer, default=0)
    sales_after = db.Column(db.Integer, default=0)
    revenue_impact = db.Column(db.Numeric(12, 2), default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='price_recommendations')
    product = db.relationship('Product', backref='price_recommendations')
    
    @classmethod
    def generate_recommendation(cls, product_id, sales_data, cost_data):
        """Generate price recommendation using AI algorithm"""
        # Simplified AI pricing algorithm
        base_markup = 1.4  # 40% markup
        
        # Adjust based on sales velocity
        if sales_data.get('velocity', 0) > 10:  # Fast moving
            recommended_markup = base_markup * 1.1
        elif sales_data.get('velocity', 0) < 2:  # Slow moving
            recommended_markup = base_markup * 0.9
        else:
            recommended_markup = base_markup
        
        cost_price = cost_data.get('cost', 0)
        recommended_price = cost_price * recommended_markup
        
        return {
            'recommended_price': recommended_price,
            'min_price': cost_price * 1.1,  # Minimum 10% profit
            'max_price': cost_price * 2.0,   # Maximum 100% markup
            'confidence': 0.75,
            'reason': f"Based on sales velocity and {recommended_markup:.1f}x markup"
        }


class QRInvoice(db.Model):
    """Invoicing via QR Code"""
    __tablename__ = 'qr_invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Invoice details
    invoice_number = db.Column(db.String(100), nullable=False, unique=True)
    customer_name = db.Column(db.String(200), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=True)
    customer_email = db.Column(db.String(200), nullable=True)
    
    # Financial details
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(3), default='KES')
    tax_amount = db.Column(db.Numeric(10, 2), default=0)
    
    # Payment methods
    mpesa_enabled = db.Column(db.Boolean, default=True)
    paypal_enabled = db.Column(db.Boolean, default=False)
    bank_transfer_enabled = db.Column(db.Boolean, default=False)
    
    # QR Code
    qr_code_data = db.Column(db.Text, nullable=False)  # QR code content
    qr_code_image_path = db.Column(db.String(500), nullable=True)
    
    # Payment tracking
    status = db.Column(db.String(20), default='pending')  # pending, paid, expired, cancelled
    payment_method_used = db.Column(db.String(30), nullable=True)
    payment_reference = db.Column(db.String(200), nullable=True)
    paid_amount = db.Column(db.Numeric(12, 2), default=0)
    
    # Expiry
    expires_at = db.Column(db.DateTime, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    company = db.relationship('Company', backref='qr_invoices')
    
    def generate_qr_code(self):
        """Generate QR code for the invoice"""
        # Create payment URL with invoice details
        payment_url = f"https://pay.yourapp.com/invoice/{self.invoice_number}"
        
        # QR code would contain payment information
        qr_data = {
            'invoice_id': self.invoice_number,
            'amount': float(self.amount),
            'currency': self.currency,
            'payment_url': payment_url,
            'expires_at': self.expires_at.isoformat()
        }
        
        self.qr_code_data = json.dumps(qr_data)
        return qr_data
    
    def mark_as_paid(self, payment_method, reference, amount=None):
        """Mark invoice as paid"""
        self.status = 'paid'
        self.payment_method_used = payment_method
        self.payment_reference = reference
        self.paid_amount = amount or self.amount
        self.paid_at = datetime.utcnow()


class MicroInvestor(db.Model):
    """Micro-Investor Tool - Allow investors to buy small shares"""
    __tablename__ = 'micro_investors'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    investor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Investment details
    shares_owned = db.Column(db.Integer, default=0)
    share_price_at_purchase = db.Column(db.Numeric(10, 2), nullable=False)
    total_invested = db.Column(db.Numeric(12, 2), default=0)
    
    # Investment terms
    investment_type = db.Column(db.String(30), default='equity')  # equity, revenue_share
    minimum_investment = db.Column(db.Numeric(10, 2), default=1000)  # KES
    expected_return_rate = db.Column(db.Float, nullable=True)  # Annual percentage
    
    # Voting rights
    voting_rights = db.Column(db.Boolean, default=False)
    voting_power_percentage = db.Column(db.Float, default=0.0)
    
    # Returns tracking
    dividends_received = db.Column(db.Numeric(12, 2), default=0)
    current_valuation = db.Column(db.Numeric(12, 2), default=0)
    return_on_investment = db.Column(db.Float, default=0.0)  # Percentage
    
    # Status
    status = db.Column(db.String(20), default='active')  # active, sold, transferred
    
    # Legal
    investment_agreement_signed = db.Column(db.Boolean, default=False)
    agreement_date = db.Column(db.Date, nullable=True)
    
    # Timestamps
    first_investment_date = db.Column(db.Date, default=datetime.utcnow)
    last_transaction_date = db.Column(db.Date, default=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='micro_investors')
    investor = db.relationship('User', backref='investments')
    
    def add_investment(self, amount, share_price):
        """Add new investment"""
        new_shares = int(amount / share_price)
        self.shares_owned += new_shares
        self.total_invested += amount
        self.last_transaction_date = datetime.utcnow().date()
        
        # Update weighted average purchase price
        if self.shares_owned > 0:
            self.share_price_at_purchase = self.total_invested / self.shares_owned
    
    def calculate_returns(self, current_share_price):
        """Calculate current returns on investment"""
        if self.total_invested > 0:
            current_value = self.shares_owned * current_share_price
            self.current_valuation = current_value
            self.return_on_investment = ((current_value + self.dividends_received - self.total_invested) / self.total_invested) * 100
        
        return self.return_on_investment


class CustomerFeedbackHeatmap(db.Model):
    """Customer Feedback Heatmap - Visual representation of feedback"""
    __tablename__ = 'feedback_heatmap'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Feedback categorization
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    service_area = db.Column(db.String(100), nullable=True)  # delivery, support, quality, etc.
    feedback_category = db.Column(db.String(50), nullable=False)  # love, complaint, suggestion
    
    # Sentiment analysis
    sentiment_score = db.Column(db.Float, default=0.0)  # -1.0 (negative) to 1.0 (positive)
    emotion_detected = db.Column(db.String(30), nullable=True)  # happy, frustrated, excited, etc.
    
    # Geographic data
    customer_location = db.Column(db.String(100), nullable=True)
    region = db.Column(db.String(50), nullable=True)
    
    # Feedback intensity
    intensity_score = db.Column(db.Float, default=0.5)  # 0.0 to 1.0
    urgency_level = db.Column(db.String(20), default='medium')  # low, medium, high
    
    # Source tracking
    feedback_source = db.Column(db.String(30), nullable=False)  # app, website, sms, call, social_media
    feedback_text = db.Column(db.Text, nullable=True)
    
    # Customer details
    customer_id = db.Column(db.Integer, nullable=True)
    customer_segment = db.Column(db.String(50), nullable=True)  # new, regular, vip
    
    # Resolution tracking
    resolved = db.Column(db.Boolean, default=False)
    resolution_time_hours = db.Column(db.Integer, nullable=True)
    
    # Timestamps
    feedback_date = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_date = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    company = db.relationship('Company', backref='feedback_heatmap')
    product = db.relationship('Product', backref='feedback_data')
    
    @classmethod
    def analyze_sentiment(cls, feedback_text):
        """Analyze sentiment of feedback text (simplified AI)"""
        # In production, this would use NLP libraries like VADER or transformers
        positive_words = ['love', 'great', 'excellent', 'amazing', 'perfect', 'good']
        negative_words = ['hate', 'terrible', 'awful', 'bad', 'poor', 'horrible']
        
        text_lower = feedback_text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return min(1.0, 0.5 + (positive_count - negative_count) * 0.2)
        elif negative_count > positive_count:
            return max(-1.0, -0.5 - (negative_count - positive_count) * 0.2)
        else:
            return 0.0
    
    @classmethod
    def get_heatmap_data(cls, company_id, days=30):
        """Get heatmap data for visualization"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        feedback_data = cls.query.filter(
            cls.company_id == company_id,
            cls.feedback_date >= start_date
        ).all()
        
        # Aggregate data for heatmap
        heatmap = {
            'sentiment_by_category': {},
            'feedback_volume_by_date': {},
            'geographic_distribution': {},
            'resolution_performance': {}
        }
        
        for feedback in feedback_data:
            # Sentiment by category
            if feedback.feedback_category not in heatmap['sentiment_by_category']:
                heatmap['sentiment_by_category'][feedback.feedback_category] = []
            heatmap['sentiment_by_category'][feedback.feedback_category].append(feedback.sentiment_score)
            
            # Volume by date
            date_key = feedback.feedback_date.strftime('%Y-%m-%d')
            if date_key not in heatmap['feedback_volume_by_date']:
                heatmap['feedback_volume_by_date'][date_key] = 0
            heatmap['feedback_volume_by_date'][date_key] += 1
            
            # Geographic distribution
            if feedback.region:
                if feedback.region not in heatmap['geographic_distribution']:
                    heatmap['geographic_distribution'][feedback.region] = {'count': 0, 'avg_sentiment': 0}
                heatmap['geographic_distribution'][feedback.region]['count'] += 1
        
        return heatmap
