"""
Enhanced Business Intelligence Models for RahaSoft ERP
Advanced analytics, reporting, and data visualization capabilities
"""

from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from extensions import db
import json
from typing import Dict, List, Any

class Dashboard(db.Model):
    """Custom dashboards for different user roles and purposes"""
    __tablename__ = 'dashboards'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    dashboard_type = Column(String(50), nullable=False)  # 'executive', 'operational', 'financial', 'sales', 'hr'
    user_id = Column(Integer, ForeignKey('user.id'))
    company_id = Column(Integer, ForeignKey('company.id'))
    is_default = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    layout_config = Column(JSON)  # Widget positions and configurations
    filters = Column(JSON)  # Default filters
    refresh_interval = Column(Integer, default=300)  # Refresh interval in seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    widgets = relationship('DashboardWidget', back_populates='dashboard', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'dashboard_type': self.dashboard_type,
            'layout_config': self.layout_config,
            'filters': self.filters,
            'refresh_interval': self.refresh_interval,
            'widgets': [widget.to_dict() for widget in self.widgets]
        }

class DashboardWidget(db.Model):
    """Individual widgets within dashboards"""
    __tablename__ = 'dashboard_widgets'
    
    id = Column(Integer, primary_key=True)
    dashboard_id = Column(Integer, ForeignKey('dashboards.id'))
    widget_type = Column(String(50), nullable=False)  # 'chart', 'table', 'kpi', 'gauge', 'map'
    title = Column(String(100), nullable=False)
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)
    width = Column(Integer, default=4)
    height = Column(Integer, default=3)
    data_source = Column(String(100))  # SQL query name or API endpoint
    chart_config = Column(JSON)  # Chart.js or other visualization config
    filters = Column(JSON)  # Widget-specific filters
    is_visible = Column(Boolean, default=True)
    refresh_rate = Column(Integer, default=60)  # Widget refresh rate in seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    dashboard = relationship('Dashboard', back_populates='widgets')
    
    def to_dict(self):
        return {
            'id': self.id,
            'widget_type': self.widget_type,
            'title': self.title,
            'position_x': self.position_x,
            'position_y': self.position_y,
            'width': self.width,
            'height': self.height,
            'data_source': self.data_source,
            'chart_config': self.chart_config,
            'filters': self.filters,
            'is_visible': self.is_visible,
            'refresh_rate': self.refresh_rate
        }

class Report(db.Model):
    """Custom reports with various output formats"""
    __tablename__ = 'reports'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    report_type = Column(String(50), nullable=False)  # 'financial', 'sales', 'inventory', 'hr', 'custom'
    category = Column(String(50))  # Additional categorization
    sql_query = Column(Text)  # Base SQL query
    parameters = Column(JSON)  # Report parameters definition
    output_format = Column(String(20), default='html')  # 'html', 'pdf', 'excel', 'csv'
    template_path = Column(String(200))  # Custom template path
    is_scheduled = Column(Boolean, default=False)
    schedule_config = Column(JSON)  # Cron-like scheduling configuration
    user_id = Column(Integer, ForeignKey('user.id'))
    company_id = Column(Integer, ForeignKey('company.id'))
    is_public = Column(Boolean, default=False)
    tags = Column(JSON)  # Report tags for organization
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_generated = Column(DateTime)
    
    # Relationships
    executions = relationship('ReportExecution', back_populates='report', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'report_type': self.report_type,
            'category': self.category,
            'parameters': self.parameters,
            'output_format': self.output_format,
            'is_scheduled': self.is_scheduled,
            'tags': self.tags,
            'last_generated': self.last_generated.isoformat() if self.last_generated else None
        }

class ReportExecution(db.Model):
    """Track report generation history"""
    __tablename__ = 'report_executions'
    
    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey('reports.id'))
    user_id = Column(Integer, ForeignKey('user.id'))
    execution_time = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='pending')  # 'pending', 'running', 'completed', 'failed'
    parameters_used = Column(JSON)  # Parameters used for this execution
    file_path = Column(String(500))  # Generated file path
    file_size = Column(Integer)  # File size in bytes
    execution_duration = Column(Float)  # Execution time in seconds
    error_message = Column(Text)  # Error details if failed
    download_count = Column(Integer, default=0)
    expires_at = Column(DateTime)  # When to clean up the file
    
    # Relationships
    report = relationship('Report', back_populates='executions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'execution_time': self.execution_time.isoformat(),
            'status': self.status,
            'parameters_used': self.parameters_used,
            'file_size': self.file_size,
            'execution_duration': self.execution_duration,
            'download_count': self.download_count,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

class KPIDefinition(db.Model):
    """Define custom Key Performance Indicators"""
    __tablename__ = 'kpi_definitions'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # 'financial', 'sales', 'operations', 'hr', 'customer'
    calculation_method = Column(String(20))  # 'sql', 'formula', 'api'
    sql_query = Column(Text)  # SQL for calculation
    formula = Column(String(500))  # Mathematical formula
    api_endpoint = Column(String(200))  # External API endpoint
    target_value = Column(Float)  # Target/goal value
    target_type = Column(String(20))  # 'higher_better', 'lower_better', 'target_range'
    unit = Column(String(20))  # 'currency', 'percentage', 'count', 'ratio'
    frequency = Column(String(20), default='daily')  # 'realtime', 'hourly', 'daily', 'weekly', 'monthly'
    company_id = Column(Integer, ForeignKey('company.id'))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    values = relationship('KPIValue', back_populates='kpi', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'target_value': self.target_value,
            'target_type': self.target_type,
            'unit': self.unit,
            'frequency': self.frequency
        }

class KPIValue(db.Model):
    """Store calculated KPI values over time"""
    __tablename__ = 'kpi_values'
    
    id = Column(Integer, primary_key=True)
    kpi_id = Column(Integer, ForeignKey('kpi_definitions.id'))
    value = Column(Float, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow)
    period_start = Column(DateTime)  # For period-based KPIs
    period_end = Column(DateTime)
    calculation_metadata = Column(JSON)  # Additional calculation details
    
    # Relationships
    kpi = relationship('KPIDefinition', back_populates='values')
    
    def to_dict(self):
        return {
            'id': self.id,
            'value': self.value,
            'calculated_at': self.calculated_at.isoformat(),
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'calculation_metadata': self.calculation_metadata
        }

class DataAlert(db.Model):
    """Define alerts based on data conditions"""
    __tablename__ = 'data_alerts'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    alert_type = Column(String(50))  # 'threshold', 'anomaly', 'trend', 'custom'
    data_source = Column(String(100))  # Table or view to monitor
    condition_sql = Column(Text)  # SQL condition for alert
    threshold_value = Column(Float)
    comparison_operator = Column(String(10))  # '>', '<', '=', '>=', '<=', '!='
    severity = Column(String(20), default='medium')  # 'low', 'medium', 'high', 'critical'
    notification_method = Column(JSON)  # Email, SMS, in-app, webhook
    recipients = Column(JSON)  # List of recipients
    is_active = Column(Boolean, default=True)
    check_frequency = Column(Integer, default=60)  # Check frequency in minutes
    company_id = Column(Integer, ForeignKey('company.id'))
    created_by = Column(Integer, ForeignKey('user.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_checked = Column(DateTime)
    last_triggered = Column(DateTime)
    
    # Relationships
    notifications = relationship('AlertNotification', back_populates='alert', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'is_active': self.is_active,
            'check_frequency': self.check_frequency,
            'last_checked': self.last_checked.isoformat() if self.last_checked else None,
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None
        }

class AlertNotification(db.Model):
    """Track sent alert notifications"""
    __tablename__ = 'alert_notifications'
    
    id = Column(Integer, primary_key=True)
    alert_id = Column(Integer, ForeignKey('data_alerts.id'))
    triggered_at = Column(DateTime, default=datetime.utcnow)
    trigger_value = Column(Float)
    message = Column(Text)
    notification_method = Column(String(20))  # 'email', 'sms', 'webhook', 'in_app'
    recipient = Column(String(200))
    status = Column(String(20), default='sent')  # 'sent', 'delivered', 'failed'
    delivered_at = Column(DateTime)
    
    # Relationships
    alert = relationship('DataAlert', back_populates='notifications')
    
    def to_dict(self):
        return {
            'id': self.id,
            'triggered_at': self.triggered_at.isoformat(),
            'trigger_value': self.trigger_value,
            'message': self.message,
            'notification_method': self.notification_method,
            'recipient': self.recipient,
            'status': self.status
        }

class DataExport(db.Model):
    """Track data export requests and files"""
    __tablename__ = 'data_exports'
    
    id = Column(Integer, primary_key=True)
    export_type = Column(String(50), nullable=False)  # 'full_backup', 'table_export', 'custom_query'
    table_name = Column(String(100))  # For table exports
    sql_query = Column(Text)  # For custom exports
    format = Column(String(20), default='csv')  # 'csv', 'excel', 'json', 'sql'
    filters = Column(JSON)  # Export filters
    user_id = Column(Integer, ForeignKey('user.id'))
    company_id = Column(Integer, ForeignKey('company.id'))
    requested_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    status = Column(String(20), default='pending')  # 'pending', 'processing', 'completed', 'failed'
    file_path = Column(String(500))
    file_size = Column(Integer)
    download_count = Column(Integer, default=0)
    expires_at = Column(DateTime)
    error_message = Column(Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'export_type': self.export_type,
            'format': self.format,
            'requested_at': self.requested_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'status': self.status,
            'file_size': self.file_size,
            'download_count': self.download_count
        }

class AnalyticsSession(db.Model):
    """Track user analytics sessions for usage insights"""
    __tablename__ = 'analytics_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    session_id = Column(String(100), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    duration_minutes = Column(Integer)
    pages_viewed = Column(JSON)  # List of pages/modules accessed
    actions_performed = Column(JSON)  # List of actions taken
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    device_type = Column(String(20))  # 'desktop', 'tablet', 'mobile'
    browser = Column(String(50))
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_minutes': self.duration_minutes,
            'pages_viewed': self.pages_viewed,
            'device_type': self.device_type,
            'browser': self.browser
        }
