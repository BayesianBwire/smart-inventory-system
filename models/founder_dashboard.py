from datetime import datetime, timedelta
from extensions import db
from sqlalchemy import func

class FounderMetrics(db.Model):
    __tablename__ = 'founder_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Date for metrics
    date = db.Column(db.Date, nullable=False, unique=True)
    
    # Company metrics
    total_companies = db.Column(db.Integer, default=0)
    active_companies = db.Column(db.Integer, default=0)
    suspended_companies = db.Column(db.Integer, default=0)
    blacklisted_companies = db.Column(db.Integer, default=0)
    new_companies = db.Column(db.Integer, default=0)
    
    # User metrics
    total_users = db.Column(db.Integer, default=0)
    active_users = db.Column(db.Integer, default=0)
    daily_logins = db.Column(db.Integer, default=0)
    
    # Financial metrics
    total_revenue = db.Column(db.Numeric(12, 2), default=0)
    monthly_recurring_revenue = db.Column(db.Numeric(12, 2), default=0)
    daily_revenue = db.Column(db.Numeric(10, 2), default=0)
    
    # Subscription metrics
    trial_subscriptions = db.Column(db.Integer, default=0)
    starter_subscriptions = db.Column(db.Integer, default=0)
    professional_subscriptions = db.Column(db.Integer, default=0)
    enterprise_subscriptions = db.Column(db.Integer, default=0)
    
    # Feature usage
    most_used_modules = db.Column(db.JSON, nullable=True)
    average_session_duration = db.Column(db.Integer, default=0)  # in minutes
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<FounderMetrics {self.date}>"
    
    @classmethod
    def get_or_create_today(cls):
        """Get or create today's founder metrics"""
        today = datetime.utcnow().date()
        metrics = cls.query.filter_by(date=today).first()
        if not metrics:
            metrics = cls(date=today)
            db.session.add(metrics)
        return metrics
    
    @classmethod
    def calculate_growth_rate(cls, days=30):
        """Calculate growth rate over specified period"""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        latest = cls.query.filter(cls.date <= end_date).order_by(cls.date.desc()).first()
        earliest = cls.query.filter(cls.date >= start_date).order_by(cls.date.asc()).first()
        
        if not latest or not earliest or earliest.active_companies == 0:
            return 0
        
        growth_rate = ((latest.active_companies - earliest.active_companies) / earliest.active_companies) * 100
        return round(growth_rate, 2)


class CompanyFeedback(db.Model):
    __tablename__ = 'company_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Feedback details
    category = db.Column(db.String(50), nullable=False)  # bug, feature_request, complaint, praise
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Additional data
    module_affected = db.Column(db.String(50), nullable=True)
    browser_info = db.Column(db.String(500), nullable=True)
    screenshot_url = db.Column(db.String(500), nullable=True)
    
    # Status tracking
    status = db.Column(db.String(20), default='open')  # open, in_progress, resolved, closed
    assigned_to = db.Column(db.String(100), nullable=True)  # Founder or support person
    
    # Founder response
    founder_response = db.Column(db.Text, nullable=True)
    response_date = db.Column(db.DateTime, nullable=True)
    
    # Rating (for resolved feedback)
    resolution_rating = db.Column(db.Integer, nullable=True)  # 1-5 stars
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    company = db.relationship('Company', backref='feedback_submissions')
    user = db.relationship('User', backref='feedback_given')
    
    def __repr__(self):
        return f"<CompanyFeedback {self.category} - {self.subject}>"
    
    def respond(self, response_message, responder='Founder'):
        """Add founder response to feedback"""
        self.founder_response = response_message
        self.response_date = datetime.utcnow()
        self.assigned_to = responder
        if self.status == 'open':
            self.status = 'in_progress'
    
    def resolve(self, resolution_message=None):
        """Mark feedback as resolved"""
        self.status = 'resolved'
        self.resolved_at = datetime.utcnow()
        if resolution_message:
            self.founder_response = resolution_message
            self.response_date = datetime.utcnow()
    
    def close(self):
        """Close feedback"""
        self.status = 'closed'
    
    @classmethod
    def get_open_feedback_count(cls):
        """Get count of open feedback items"""
        return cls.query.filter(cls.status.in_(['open', 'in_progress'])).count()
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_name': self.company.name if self.company else None,
            'user_name': self.user.full_name if self.user else None,
            'category': self.category,
            'priority': self.priority,
            'subject': self.subject,
            'message': self.message,
            'status': self.status,
            'founder_response': self.founder_response,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'response_date': self.response_date.isoformat() if self.response_date else None
        }


class SystemAlert(db.Model):
    __tablename__ = 'system_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Alert details
    alert_type = db.Column(db.String(50), nullable=False)  # security, performance, payment, etc.
    severity = db.Column(db.String(20), nullable=False)  # low, medium, high, critical
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Affected resources
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Alert data
    alert_data = db.Column(db.JSON, nullable=True)
    threshold_value = db.Column(db.String(100), nullable=True)
    current_value = db.Column(db.String(100), nullable=True)
    
    # Status
    status = db.Column(db.String(20), default='active')  # active, acknowledged, resolved
    acknowledged_by = db.Column(db.String(100), nullable=True)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    
    # Auto-resolution
    auto_resolve = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='system_alerts')
    user = db.relationship('User', backref='user_alerts')
    
    def __repr__(self):
        return f"<SystemAlert {self.alert_type} - {self.severity}>"
    
    def acknowledge(self, acknowledger='System'):
        """Acknowledge the alert"""
        self.status = 'acknowledged'
        self.acknowledged_by = acknowledger
        self.acknowledged_at = datetime.utcnow()
    
    def resolve(self):
        """Resolve the alert"""
        self.status = 'resolved'
        self.resolved_at = datetime.utcnow()
    
    @classmethod
    def create_alert(cls, alert_type, severity, title, description, 
                    company_id=None, user_id=None, alert_data=None):
        """Create a new system alert"""
        alert = cls(
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            company_id=company_id,
            user_id=user_id,
            alert_data=alert_data
        )
        db.session.add(alert)
        return alert
    
    @classmethod
    def get_critical_alerts(cls):
        """Get all critical unresolved alerts"""
        return cls.query.filter(
            cls.severity == 'critical',
            cls.status != 'resolved'
        ).all()
    
    @classmethod
    def get_dashboard_data(cls):
        """Get comprehensive dashboard data for founder"""
        from models.ai_features import DocumentTemplate, GeneratedDocument, DebtTracker, VoiceNote, TeamVoting, BusinessMilestone
        from models.advanced_features import PayrollAutomation, PriceRecommendation, QRInvoice, MicroInvestor, CustomerFeedbackHeatmap
        from models.user import User
        from models.company import Company
        from models.subscription import Subscription
        
        # Basic metrics
        total_companies = Company.query.count()
        active_companies = Company.query.filter_by(status='active').count()
        total_users = User.query.count()
        
        # AI Feature Usage Metrics
        ai_metrics = {
            'document_generation': {
                'templates': DocumentTemplate.query.count(),
                'generated_docs': GeneratedDocument.query.count(),
                'recent_generations': GeneratedDocument.query.filter(
                    GeneratedDocument.created_at >= datetime.utcnow() - timedelta(days=7)
                ).count()
            },
            'debt_tracking': {
                'total_trackers': DebtTracker.query.count(),
                'overdue_invoices': DebtTracker.query.filter(
                    DebtTracker.status == 'overdue'
                ).count(),
                'auto_reminders_sent': DebtTracker.query.filter(
                    DebtTracker.reminder_count > 0
                ).count()
            },
            'voice_notes': {
                'total_notes': VoiceNote.query.count(),
                'pending_tasks': VoiceNote.query.filter(
                    VoiceNote.task_status == 'pending'
                ).count(),
                'completed_tasks': VoiceNote.query.filter(
                    VoiceNote.task_status == 'completed'
                ).count()
            },
            'team_voting': {
                'active_votes': TeamVoting.query.filter(
                    TeamVoting.status == 'active'
                ).count(),
                'completed_votes': TeamVoting.query.filter(
                    TeamVoting.status == 'completed'
                ).count(),
                'participation_rate': cls._calculate_voting_participation()
            },
            'milestones': {
                'total_milestones': BusinessMilestone.query.count(),
                'completed_milestones': BusinessMilestone.query.filter(
                    BusinessMilestone.status == 'completed'
                ).count(),
                'active_milestones': BusinessMilestone.query.filter(
                    BusinessMilestone.status == 'in_progress'
                ).count()
            },
            'payroll_automation': {
                'automated_payrolls': PayrollAutomation.query.filter(
                    PayrollAutomation.is_active == True
                ).count(),
                'successful_payments': PayrollAutomation.query.filter(
                    PayrollAutomation.last_execution_status == 'success'
                ).count()
            },
            'smart_pricing': {
                'price_recommendations': PriceRecommendation.query.count(),
                'accepted_recommendations': PriceRecommendation.query.filter(
                    PriceRecommendation.is_accepted == True
                ).count(),
                'avg_profit_increase': cls._calculate_avg_profit_increase()
            },
            'qr_invoicing': {
                'qr_invoices': QRInvoice.query.count(),
                'paid_invoices': QRInvoice.query.filter(
                    QRInvoice.payment_status == 'paid'
                ).count(),
                'payment_success_rate': cls._calculate_qr_payment_success_rate()
            },
            'micro_investors': {
                'total_investors': MicroInvestor.query.count(),
                'active_investors': MicroInvestor.query.filter(
                    MicroInvestor.is_active == True
                ).count(),
                'total_investment': cls._calculate_total_investment()
            },
            'feedback_heatmap': {
                'feedback_entries': CustomerFeedbackHeatmap.query.count(),
                'satisfaction_score': cls._calculate_avg_satisfaction(),
                'top_complaints': cls._get_top_complaints(),
                'top_praises': cls._get_top_praises()
            }
        }
        
        return {
            'basic_metrics': {
                'total_companies': total_companies,
                'active_companies': active_companies,
                'total_users': total_users,
                'growth_rate': cls.calculate_growth_rate()
            },
            'ai_metrics': ai_metrics,
            'alerts': cls.get_critical_alerts(),
            'recent_feedback': CompanyFeedback.query.filter(
                CompanyFeedback.status.in_(['open', 'in_progress'])
            ).order_by(CompanyFeedback.created_at.desc()).limit(5).all()
        }
    
    @classmethod
    def _calculate_voting_participation(cls):
        """Calculate average voting participation rate"""
        from models.ai_features import TeamVoting
        try:
            total_votes = TeamVoting.query.count()
            if total_votes == 0:
                return 0
            
            # Calculate average participation across all votes
            avg_participation = db.session.query(
                func.avg(TeamVoting.total_votes)
            ).scalar() or 0
            
            return round(avg_participation, 2)
        except:
            return 0
    
    @classmethod
    def _calculate_avg_profit_increase(cls):
        """Calculate average profit increase from price recommendations"""
        from models.advanced_features import PriceRecommendation
        try:
            accepted_recs = PriceRecommendation.query.filter(
                PriceRecommendation.is_accepted == True,
                PriceRecommendation.profit_increase.isnot(None)
            ).all()
            
            if not accepted_recs:
                return 0
            
            total_increase = sum(rec.profit_increase for rec in accepted_recs)
            return round(total_increase / len(accepted_recs), 2)
        except:
            return 0
    
    @classmethod
    def _calculate_qr_payment_success_rate(cls):
        """Calculate QR invoice payment success rate"""
        from models.advanced_features import QRInvoice
        try:
            total_invoices = QRInvoice.query.count()
            if total_invoices == 0:
                return 0
            
            paid_invoices = QRInvoice.query.filter(
                QRInvoice.payment_status == 'paid'
            ).count()
            
            return round((paid_invoices / total_invoices) * 100, 2)
        except:
            return 0
    
    @classmethod
    def _calculate_total_investment(cls):
        """Calculate total micro-investment amount"""
        from models.advanced_features import MicroInvestor
        try:
            total = db.session.query(
                func.sum(MicroInvestor.investment_amount)
            ).scalar() or 0
            return float(total)
        except:
            return 0
    
    @classmethod
    def _calculate_avg_satisfaction(cls):
        """Calculate average customer satisfaction score"""
        from models.advanced_features import CustomerFeedbackHeatmap
        try:
            avg_score = db.session.query(
                func.avg(CustomerFeedbackHeatmap.satisfaction_score)
            ).scalar() or 0
            return round(float(avg_score), 2)
        except:
            return 0
    
    @classmethod
    def _get_top_complaints(cls, limit=5):
        """Get top customer complaints"""
        from models.advanced_features import CustomerFeedbackHeatmap
        try:
            complaints = CustomerFeedbackHeatmap.query.filter(
                CustomerFeedbackHeatmap.feedback_type == 'complaint'
            ).order_by(
                CustomerFeedbackHeatmap.impact_score.desc()
            ).limit(limit).all()
            
            return [{'category': c.category, 'impact_score': c.impact_score} for c in complaints]
        except:
            return []
    
    @classmethod
    def _get_top_praises(cls, limit=5):
        """Get top customer praises"""
        from models.advanced_features import CustomerFeedbackHeatmap
        try:
            praises = CustomerFeedbackHeatmap.query.filter(
                CustomerFeedbackHeatmap.feedback_type == 'praise'
            ).order_by(
                CustomerFeedbackHeatmap.impact_score.desc()
            ).limit(limit).all()
            
            return [{'category': p.category, 'impact_score': p.impact_score} for p in praises]
        except:
            return []
    
    @classmethod
    def get_ai_usage_analytics(cls):
        """Get detailed AI feature usage analytics"""
        from models.ai_features import DocumentTemplate, GeneratedDocument, DebtTracker, VoiceNote, TeamVoting, BusinessMilestone
        
        # Document generation analytics
        doc_analytics = {
            'popular_templates': db.session.query(
                DocumentTemplate.template_type,
                func.count(GeneratedDocument.id).label('usage_count')
            ).join(GeneratedDocument).group_by(
                DocumentTemplate.template_type
            ).order_by(func.count(GeneratedDocument.id).desc()).limit(5).all(),
            
            'generation_trends': db.session.query(
                func.date(GeneratedDocument.created_at).label('date'),
                func.count(GeneratedDocument.id).label('count')
            ).filter(
                GeneratedDocument.created_at >= datetime.utcnow() - timedelta(days=30)
            ).group_by(func.date(GeneratedDocument.created_at)).all()
        }
        
        # Debt tracking analytics
        debt_analytics = {
            'recovery_rate': cls._calculate_debt_recovery_rate(),
            'avg_recovery_time': cls._calculate_avg_recovery_time(),
            'reminder_effectiveness': cls._calculate_reminder_effectiveness()
        }
        
        # Voice notes analytics
        voice_analytics = {
            'task_completion_rate': cls._calculate_task_completion_rate(),
            'avg_processing_time': cls._calculate_avg_processing_time(),
            'popular_task_types': cls._get_popular_task_types()
        }
        
        return {
            'document_generation': doc_analytics,
            'debt_tracking': debt_analytics,
            'voice_notes': voice_analytics
        }
    
    @classmethod
    def _calculate_debt_recovery_rate(cls):
        """Calculate debt recovery success rate"""
        from models.ai_features import DebtTracker
        try:
            total_debts = DebtTracker.query.count()
            if total_debts == 0:
                return 0
            
            recovered_debts = DebtTracker.query.filter(
                DebtTracker.status == 'paid'
            ).count()
            
            return round((recovered_debts / total_debts) * 100, 2)
        except:
            return 0
    
    @classmethod
    def _calculate_avg_recovery_time(cls):
        """Calculate average debt recovery time in days"""
        from models.ai_features import DebtTracker
        try:
            recovered_debts = DebtTracker.query.filter(
                DebtTracker.status == 'paid',
                DebtTracker.payment_date.isnot(None)
            ).all()
            
            if not recovered_debts:
                return 0
            
            total_days = sum(
                (debt.payment_date - debt.due_date).days 
                for debt in recovered_debts 
                if debt.payment_date and debt.due_date
            )
            
            return round(total_days / len(recovered_debts), 1) if recovered_debts else 0
        except:
            return 0
    
    @classmethod
    def _calculate_reminder_effectiveness(cls):
        """Calculate reminder effectiveness rate"""
        from models.ai_features import DebtTracker
        try:
            debts_with_reminders = DebtTracker.query.filter(
                DebtTracker.reminder_count > 0
            ).count()
            
            if debts_with_reminders == 0:
                return 0
            
            paid_after_reminders = DebtTracker.query.filter(
                DebtTracker.reminder_count > 0,
                DebtTracker.status == 'paid'
            ).count()
            
            return round((paid_after_reminders / debts_with_reminders) * 100, 2)
        except:
            return 0
    
    @classmethod
    def _calculate_task_completion_rate(cls):
        """Calculate voice note task completion rate"""
        from models.ai_features import VoiceNote
        try:
            total_tasks = VoiceNote.query.filter(
                VoiceNote.task_extracted == True
            ).count()
            
            if total_tasks == 0:
                return 0
            
            completed_tasks = VoiceNote.query.filter(
                VoiceNote.task_status == 'completed'
            ).count()
            
            return round((completed_tasks / total_tasks) * 100, 2)
        except:
            return 0
    
    @classmethod
    def _calculate_avg_processing_time(cls):
        """Calculate average voice note processing time"""
        from models.ai_features import VoiceNote
        try:
            processed_notes = VoiceNote.query.filter(
                VoiceNote.processing_time.isnot(None)
            ).all()
            
            if not processed_notes:
                return 0
            
            total_time = sum(note.processing_time for note in processed_notes)
            return round(total_time / len(processed_notes), 2)
        except:
            return 0
    
    @classmethod
    def _get_popular_task_types(cls, limit=5):
        """Get most popular task types from voice notes"""
        from models.ai_features import VoiceNote
        try:
            task_types = db.session.query(
                VoiceNote.task_type,
                func.count(VoiceNote.id).label('count')
            ).filter(
                VoiceNote.task_type.isnot(None)
            ).group_by(VoiceNote.task_type).order_by(
                func.count(VoiceNote.id).desc()
            ).limit(limit).all()
            
            return [{'type': tt[0], 'count': tt[1]} for tt in task_types]
        except:
            return []
    
    @classmethod
    def get_business_insights(cls):
        """Get AI-powered business insights for founder dashboard"""
        insights = []
        
        try:
            # Revenue insights
            revenue_insight = cls._generate_revenue_insight()
            if revenue_insight:
                insights.append(revenue_insight)
            
            # User engagement insights
            engagement_insight = cls._generate_engagement_insight()
            if engagement_insight:
                insights.append(engagement_insight)
            
            # Feature adoption insights
            adoption_insight = cls._generate_adoption_insight()
            if adoption_insight:
                insights.append(adoption_insight)
            
            # Performance insights
            performance_insight = cls._generate_performance_insight()
            if performance_insight:
                insights.append(performance_insight)
            
        except Exception as e:
            insights.append({
                'type': 'error',
                'title': 'Insights Generation Error',
                'message': 'Unable to generate insights at this time.',
                'severity': 'low'
            })
        
        return insights
    
    @classmethod
    def _generate_revenue_insight(cls):
        """Generate revenue-related insights"""
        from models.subscription import Subscription
        from models.company import Company
        
        # Calculate conversion rate
        total_companies = Company.query.count()
        paying_companies = Subscription.query.filter(
            Subscription.status == 'active',
            Subscription.plan_type != 'trial'
        ).count()
        
        if total_companies > 0:
            conversion_rate = (paying_companies / total_companies) * 100
            
            if conversion_rate < 10:
                return {
                    'type': 'revenue',
                    'title': 'Low Conversion Rate Alert',
                    'message': f'Only {conversion_rate:.1f}% of companies are on paid plans. Consider improving trial experience or offering incentives.',
                    'severity': 'high',
                    'metric': conversion_rate
                }
            elif conversion_rate > 25:
                return {
                    'type': 'revenue',
                    'title': 'Excellent Conversion Rate',
                    'message': f'Great job! {conversion_rate:.1f}% conversion rate is above industry average.',
                    'severity': 'positive',
                    'metric': conversion_rate
                }
        
        return None
    
    @classmethod
    def _generate_engagement_insight(cls):
        """Generate user engagement insights"""
        from models.user import User
        
        # Calculate recent login rate
        week_ago = datetime.utcnow() - timedelta(days=7)
        total_users = User.query.count()
        recent_users = User.query.filter(
            User.last_login >= week_ago
        ).count() if hasattr(User, 'last_login') else 0
        
        if total_users > 0:
            engagement_rate = (recent_users / total_users) * 100
            
            if engagement_rate < 30:
                return {
                    'type': 'engagement',
                    'title': 'Low User Engagement',
                    'message': f'Only {engagement_rate:.1f}% of users logged in this week. Consider re-engagement campaigns.',
                    'severity': 'medium',
                    'metric': engagement_rate
                }
        
        return None
    
    @classmethod
    def _generate_adoption_insight(cls):
        """Generate feature adoption insights"""
        from models.ai_features import GeneratedDocument, VoiceNote
        
        # Check AI feature adoption
        total_docs = GeneratedDocument.query.count()
        total_voice_notes = VoiceNote.query.count()
        
        if total_docs < 10 and total_voice_notes < 10:
            return {
                'type': 'adoption',
                'title': 'Low AI Feature Adoption',
                'message': 'AI features are underutilized. Consider providing tutorials or demos to users.',
                'severity': 'medium',
                'metric': total_docs + total_voice_notes
            }
        
        return None
    
    @classmethod
    def _generate_performance_insight(cls):
        """Generate system performance insights"""
        # Check for critical alerts
        critical_alerts = cls.get_critical_alerts()
        
        if len(critical_alerts) > 0:
            return {
                'type': 'performance',
                'title': 'Critical System Alerts',
                'message': f'{len(critical_alerts)} critical alerts require immediate attention.',
                'severity': 'critical',
                'metric': len(critical_alerts)
            }
        
        return None
