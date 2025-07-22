"""
Business Intelligence Routes for RahaSoft ERP
Advanced analytics, dashboards, reports, and data visualization
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, text, desc, asc
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
import json
import pandas as pd
import io
import os
from extensions import db
from models.business_intelligence_enhanced import (
    Dashboard, DashboardWidget, Report, ReportExecution, 
    KPIDefinition, KPIValue, DataAlert, AlertNotification,
    DataExport, AnalyticsSession
)
from models.user import User
from models.company import Company
from models.sale import Sale
from models.product import Product
from models.employee import Employee
from utils.permissions import has_permission
from utils.cache_manager import redis_manager

bi_bp = Blueprint('business_intelligence', __name__, url_prefix='/bi')

# ============================================================================
# DASHBOARD MANAGEMENT
# ============================================================================

@bi_bp.route('/dashboards')
@login_required
def dashboards():
    """List all available dashboards"""
    user_dashboards = Dashboard.query.filter_by(
        company_id=current_user.company_id
    ).order_by(Dashboard.name).all()
    
    public_dashboards = Dashboard.query.filter_by(
        is_public=True
    ).order_by(Dashboard.name).all()
    
    return render_template('bi/dashboards.html',
                         user_dashboards=user_dashboards,
                         public_dashboards=public_dashboards)

@bi_bp.route('/dashboard/<int:dashboard_id>')
@login_required
def view_dashboard(dashboard_id):
    """View a specific dashboard"""
    dashboard = Dashboard.query.get_or_404(dashboard_id)
    
    # Check permissions
    if dashboard.company_id != current_user.company_id and not dashboard.is_public:
        flash('Access denied to this dashboard.', 'error')
        return redirect(url_for('business_intelligence.dashboards'))
    
    # Get widgets with their data
    widgets_data = []
    for widget in dashboard.widgets:
        if widget.is_visible:
            widget_data = widget.to_dict()
            # Fetch actual data for the widget
            widget_data['data'] = get_widget_data(widget)
            widgets_data.append(widget_data)
    
    return render_template('bi/dashboard_view.html',
                         dashboard=dashboard,
                         widgets=widgets_data)

@bi_bp.route('/dashboard/create', methods=['GET', 'POST'])
@login_required
def create_dashboard():
    """Create a new dashboard"""
    if not has_permission(current_user, 'create_dashboard'):
        flash('Permission denied.', 'error')
        return redirect(url_for('business_intelligence.dashboards'))
    
    if request.method == 'POST':
        try:
            dashboard = Dashboard(
                name=request.form['name'],
                description=request.form.get('description'),
                dashboard_type=request.form['dashboard_type'],
                user_id=current_user.id,
                company_id=current_user.company_id,
                is_public=request.form.get('is_public') == 'on',
                refresh_interval=int(request.form.get('refresh_interval', 300))
            )
            
            db.session.add(dashboard)
            db.session.commit()
            
            flash(f'Dashboard "{dashboard.name}" created successfully!', 'success')
            return redirect(url_for('business_intelligence.edit_dashboard', dashboard_id=dashboard.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating dashboard: {str(e)}', 'error')
    
    return render_template('bi/dashboard_create.html')

@bi_bp.route('/dashboard/<int:dashboard_id>/edit')
@login_required
def edit_dashboard(dashboard_id):
    """Edit dashboard layout and widgets"""
    dashboard = Dashboard.query.get_or_404(dashboard_id)
    
    # Check permissions
    if dashboard.user_id != current_user.id and current_user.role not in ['admin', 'founder']:
        flash('Permission denied.', 'error')
        return redirect(url_for('business_intelligence.dashboards'))
    
    available_widgets = get_available_widget_types()
    data_sources = get_available_data_sources()
    
    return render_template('bi/dashboard_edit.html',
                         dashboard=dashboard,
                         available_widgets=available_widgets,
                         data_sources=data_sources)

@bi_bp.route('/api/dashboard/<int:dashboard_id>/widgets', methods=['POST'])
@login_required
def add_widget(dashboard_id):
    """Add a widget to a dashboard"""
    dashboard = Dashboard.query.get_or_404(dashboard_id)
    
    # Check permissions
    if dashboard.user_id != current_user.id and current_user.role not in ['admin', 'founder']:
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        widget = DashboardWidget(
            dashboard_id=dashboard_id,
            widget_type=request.json['widget_type'],
            title=request.json['title'],
            position_x=request.json.get('position_x', 0),
            position_y=request.json.get('position_y', 0),
            width=request.json.get('width', 4),
            height=request.json.get('height', 3),
            data_source=request.json.get('data_source'),
            chart_config=request.json.get('chart_config', {}),
            filters=request.json.get('filters', {})
        )
        
        db.session.add(widget)
        db.session.commit()
        
        return jsonify(widget.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bi_bp.route('/api/widget/<int:widget_id>/data')
@login_required
def get_widget_data_api(widget_id):
    """Get data for a specific widget"""
    widget = DashboardWidget.query.get_or_404(widget_id)
    
    # Check permissions
    dashboard = widget.dashboard
    if dashboard.company_id != current_user.company_id and not dashboard.is_public:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        data = get_widget_data(widget)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# REPORTS MANAGEMENT
# ============================================================================

@bi_bp.route('/reports')
@login_required
def reports():
    """List all available reports"""
    user_reports = Report.query.filter_by(
        company_id=current_user.company_id
    ).order_by(Report.name).all()
    
    public_reports = Report.query.filter_by(
        is_public=True
    ).order_by(Report.name).all()
    
    return render_template('bi/reports.html',
                         user_reports=user_reports,
                         public_reports=public_reports)

@bi_bp.route('/report/create', methods=['GET', 'POST'])
@login_required
def create_report():
    """Create a new report"""
    if not has_permission(current_user, 'create_report'):
        flash('Permission denied.', 'error')
        return redirect(url_for('business_intelligence.reports'))
    
    if request.method == 'POST':
        try:
            report = Report(
                name=request.form['name'],
                description=request.form.get('description'),
                report_type=request.form['report_type'],
                category=request.form.get('category'),
                sql_query=request.form.get('sql_query'),
                parameters=json.loads(request.form.get('parameters', '{}')),
                output_format=request.form.get('output_format', 'html'),
                user_id=current_user.id,
                company_id=current_user.company_id,
                is_public=request.form.get('is_public') == 'on',
                tags=request.form.get('tags', '').split(',')
            )
            
            db.session.add(report)
            db.session.commit()
            
            flash(f'Report "{report.name}" created successfully!', 'success')
            return redirect(url_for('business_intelligence.reports'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating report: {str(e)}', 'error')
    
    return render_template('bi/report_create.html')

@bi_bp.route('/report/<int:report_id>/generate')
@login_required
def generate_report(report_id):
    """Generate a report"""
    report = Report.query.get_or_404(report_id)
    
    # Check permissions
    if report.company_id != current_user.company_id and not report.is_public:
        flash('Access denied to this report.', 'error')
        return redirect(url_for('business_intelligence.reports'))
    
    try:
        # Create report execution record
        execution = ReportExecution(
            report_id=report_id,
            user_id=current_user.id,
            status='running',
            parameters_used=request.args.to_dict()
        )
        db.session.add(execution)
        db.session.commit()
        
        # Generate the report
        start_time = datetime.utcnow()
        
        # Execute the report query
        if report.sql_query:
            # Replace parameters in query
            query = report.sql_query
            for param, value in request.args.items():
                query = query.replace(f':{param}', f"'{value}'")
            
            result = db.session.execute(text(query))
            data = result.fetchall()
            columns = result.keys()
            
            # Convert to DataFrame for easier manipulation
            df = pd.DataFrame(data, columns=columns)
            
            # Generate output based on format
            if report.output_format == 'csv':
                output = df.to_csv(index=False)
                mimetype = 'text/csv'
                filename = f"{report.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            elif report.output_format == 'excel':
                output = io.BytesIO()
                df.to_excel(output, index=False)
                output.seek(0)
                mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                filename = f"{report.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            else:  # HTML
                output = df.to_html(classes='table table-striped table-hover')
                mimetype = 'text/html'
                filename = f"{report.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            # Update execution record
            end_time = datetime.utcnow()
            execution.status = 'completed'
            execution.completed_at = end_time
            execution.execution_duration = (end_time - start_time).total_seconds()
            execution.file_size = len(str(output)) if isinstance(output, str) else len(output.getvalue())
            execution.expires_at = datetime.utcnow() + timedelta(days=7)
            
            # Save file if not HTML
            if report.output_format != 'html':
                file_dir = os.path.join(current_app.instance_path, 'reports')
                os.makedirs(file_dir, exist_ok=True)
                file_path = os.path.join(file_dir, filename)
                
                if isinstance(output, str):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(output)
                else:
                    with open(file_path, 'wb') as f:
                        f.write(output.getvalue())
                
                execution.file_path = file_path
            
            db.session.commit()
            
            # Return the report
            if report.output_format == 'html':
                return render_template('bi/report_result.html',
                                     report=report,
                                     data=output,
                                     execution=execution)
            else:
                return send_file(
                    execution.file_path,
                    mimetype=mimetype,
                    as_attachment=True,
                    download_name=filename
                )
                
        else:
            flash('Report has no query defined.', 'error')
            return redirect(url_for('business_intelligence.reports'))
            
    except Exception as e:
        execution.status = 'failed'
        execution.error_message = str(e)
        db.session.commit()
        flash(f'Error generating report: {str(e)}', 'error')
        return redirect(url_for('business_intelligence.reports'))

# ============================================================================
# KPI MANAGEMENT
# ============================================================================

@bi_bp.route('/kpis')
@login_required
def kpis():
    """List and display KPIs"""
    company_kpis = KPIDefinition.query.filter_by(
        company_id=current_user.company_id,
        is_active=True
    ).all()
    
    # Get latest values for each KPI
    kpi_data = []
    for kpi in company_kpis:
        latest_value = KPIValue.query.filter_by(
            kpi_id=kpi.id
        ).order_by(KPIValue.calculated_at.desc()).first()
        
        kpi_dict = kpi.to_dict()
        kpi_dict['current_value'] = latest_value.value if latest_value else 0
        kpi_dict['last_updated'] = latest_value.calculated_at if latest_value else None
        
        # Calculate trend (comparison with previous value)
        if latest_value:
            previous_value = KPIValue.query.filter_by(
                kpi_id=kpi.id
            ).filter(
                KPIValue.calculated_at < latest_value.calculated_at
            ).order_by(KPIValue.calculated_at.desc()).first()
            
            if previous_value:
                change = latest_value.value - previous_value.value
                kpi_dict['trend'] = 'up' if change > 0 else 'down' if change < 0 else 'stable'
                kpi_dict['change_value'] = change
                kpi_dict['change_percentage'] = (change / previous_value.value * 100) if previous_value.value != 0 else 0
            else:
                kpi_dict['trend'] = 'stable'
                kpi_dict['change_value'] = 0
                kpi_dict['change_percentage'] = 0
        
        kpi_data.append(kpi_dict)
    
    return render_template('bi/kpis.html', kpis=kpi_data)

@bi_bp.route('/kpi/create', methods=['GET', 'POST'])
@login_required
def create_kpi():
    """Create a new KPI definition"""
    if not has_permission(current_user, 'create_kpi'):
        flash('Permission denied.', 'error')
        return redirect(url_for('business_intelligence.kpis'))
    
    if request.method == 'POST':
        try:
            kpi = KPIDefinition(
                name=request.form['name'],
                description=request.form.get('description'),
                category=request.form['category'],
                calculation_method=request.form['calculation_method'],
                sql_query=request.form.get('sql_query'),
                formula=request.form.get('formula'),
                target_value=float(request.form.get('target_value', 0)),
                target_type=request.form.get('target_type', 'higher_better'),
                unit=request.form.get('unit', 'count'),
                frequency=request.form.get('frequency', 'daily'),
                company_id=current_user.company_id
            )
            
            db.session.add(kpi)
            db.session.commit()
            
            # Calculate initial value
            calculate_kpi_value(kpi)
            
            flash(f'KPI "{kpi.name}" created successfully!', 'success')
            return redirect(url_for('business_intelligence.kpis'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating KPI: {str(e)}', 'error')
    
    return render_template('bi/kpi_create.html')

@bi_bp.route('/api/kpi/<int:kpi_id>/history')
@login_required
def get_kpi_history(kpi_id):
    """Get historical values for a KPI"""
    kpi = KPIDefinition.query.get_or_404(kpi_id)
    
    if kpi.company_id != current_user.company_id:
        return jsonify({'error': 'Access denied'}), 403
    
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)
    
    values = KPIValue.query.filter_by(
        kpi_id=kpi_id
    ).filter(
        KPIValue.calculated_at >= since
    ).order_by(KPIValue.calculated_at).all()
    
    return jsonify({
        'kpi': kpi.to_dict(),
        'values': [value.to_dict() for value in values]
    })

# ============================================================================
# ANALYTICS & INSIGHTS
# ============================================================================

@bi_bp.route('/analytics')
@login_required
def analytics():
    """Main analytics overview"""
    # Get company overview statistics
    company_stats = get_company_analytics(current_user.company_id)
    
    # Get user activity analytics
    user_activity = get_user_activity_analytics(current_user.company_id)
    
    # Get recent alerts
    recent_alerts = DataAlert.query.filter_by(
        company_id=current_user.company_id
    ).order_by(DataAlert.last_triggered.desc()).limit(5).all()
    
    return render_template('bi/analytics.html',
                         company_stats=company_stats,
                         user_activity=user_activity,
                         recent_alerts=recent_alerts)

@bi_bp.route('/api/analytics/sales-trend')
@login_required
def sales_trend_api():
    """Get sales trend data"""
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)
    
    sales_data = db.session.query(
        func.date(Sale.date_created).label('date'),
        func.sum(Sale.total_amount).label('total'),
        func.count(Sale.id).label('count')
    ).filter(
        Sale.company_id == current_user.company_id,
        Sale.date_created >= since
    ).group_by(
        func.date(Sale.date_created)
    ).order_by('date').all()
    
    return jsonify([{
        'date': row.date.isoformat(),
        'total': float(row.total or 0),
        'count': row.count
    } for row in sales_data])

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_widget_data(widget):
    """Get data for a specific widget"""
    try:
        if widget.data_source == 'sales_summary':
            return get_sales_summary_data(widget.filters)
        elif widget.data_source == 'top_products':
            return get_top_products_data(widget.filters)
        elif widget.data_source == 'revenue_trend':
            return get_revenue_trend_data(widget.filters)
        elif widget.data_source == 'employee_stats':
            return get_employee_stats_data(widget.filters)
        elif widget.data_source == 'custom_sql' and widget.chart_config.get('sql'):
            return execute_custom_sql(widget.chart_config['sql'])
        else:
            return {'error': 'Unknown data source'}
    except Exception as e:
        return {'error': str(e)}

def get_sales_summary_data(filters):
    """Get sales summary data"""
    query = Sale.query.filter_by(company_id=current_user.company_id)
    
    if filters.get('date_from'):
        query = query.filter(Sale.date_created >= filters['date_from'])
    if filters.get('date_to'):
        query = query.filter(Sale.date_created <= filters['date_to'])
    
    sales = query.all()
    
    return {
        'total_sales': len(sales),
        'total_revenue': sum(sale.total_amount for sale in sales),
        'average_sale': sum(sale.total_amount for sale in sales) / len(sales) if sales else 0
    }

def get_top_products_data(filters):
    """Get top selling products data"""
    limit = filters.get('limit', 10)
    
    # This would need to be implemented based on your sale items structure
    # For now, returning mock data
    return {
        'labels': ['Product A', 'Product B', 'Product C'],
        'data': [150, 120, 90]
    }

def get_revenue_trend_data(filters):
    """Get revenue trend data"""
    days = filters.get('days', 30)
    since = datetime.utcnow() - timedelta(days=days)
    
    trend_data = db.session.query(
        func.date(Sale.date_created).label('date'),
        func.sum(Sale.total_amount).label('revenue')
    ).filter(
        Sale.company_id == current_user.company_id,
        Sale.date_created >= since
    ).group_by(
        func.date(Sale.date_created)
    ).order_by('date').all()
    
    return {
        'labels': [row.date.isoformat() for row in trend_data],
        'data': [float(row.revenue or 0) for row in trend_data]
    }

def get_employee_stats_data(filters):
    """Get employee statistics"""
    total_employees = Employee.query.filter_by(company_id=current_user.company_id).count()
    active_employees = Employee.query.filter_by(
        company_id=current_user.company_id,
        status='active'
    ).count()
    
    return {
        'total': total_employees,
        'active': active_employees,
        'inactive': total_employees - active_employees
    }

def execute_custom_sql(sql_query):
    """Execute custom SQL query safely"""
    try:
        # Add basic SQL injection protection
        if any(keyword in sql_query.upper() for keyword in ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER']):
            return {'error': 'Destructive SQL operations not allowed'}
        
        result = db.session.execute(text(sql_query))
        data = result.fetchall()
        columns = result.keys()
        
        return {
            'columns': list(columns),
            'data': [list(row) for row in data]
        }
    except Exception as e:
        return {'error': str(e)}

def get_available_widget_types():
    """Get list of available widget types"""
    return [
        {'id': 'line_chart', 'name': 'Line Chart', 'icon': 'fas fa-chart-line'},
        {'id': 'bar_chart', 'name': 'Bar Chart', 'icon': 'fas fa-chart-bar'},
        {'id': 'pie_chart', 'name': 'Pie Chart', 'icon': 'fas fa-chart-pie'},
        {'id': 'kpi_card', 'name': 'KPI Card', 'icon': 'fas fa-tachometer-alt'},
        {'id': 'data_table', 'name': 'Data Table', 'icon': 'fas fa-table'},
        {'id': 'gauge', 'name': 'Gauge', 'icon': 'fas fa-gauge'},
        {'id': 'map', 'name': 'Map', 'icon': 'fas fa-map'},
        {'id': 'custom', 'name': 'Custom Widget', 'icon': 'fas fa-cogs'}
    ]

def get_available_data_sources():
    """Get list of available data sources"""
    return [
        {'id': 'sales_summary', 'name': 'Sales Summary'},
        {'id': 'top_products', 'name': 'Top Products'},
        {'id': 'revenue_trend', 'name': 'Revenue Trend'},
        {'id': 'employee_stats', 'name': 'Employee Statistics'},
        {'id': 'custom_sql', 'name': 'Custom SQL Query'}
    ]

def calculate_kpi_value(kpi):
    """Calculate and store a KPI value"""
    try:
        if kpi.calculation_method == 'sql' and kpi.sql_query:
            result = db.session.execute(text(kpi.sql_query))
            value = result.scalar()
            
            kpi_value = KPIValue(
                kpi_id=kpi.id,
                value=float(value or 0),
                calculated_at=datetime.utcnow()
            )
            
            db.session.add(kpi_value)
            db.session.commit()
            
            return kpi_value
    except Exception as e:
        print(f"Error calculating KPI {kpi.name}: {str(e)}")
        return None

def get_company_analytics(company_id):
    """Get company-wide analytics"""
    total_users = User.query.filter_by(company_id=company_id).count()
    total_products = Product.query.filter_by(company_id=company_id).count()
    total_sales = Sale.query.filter_by(company_id=company_id).count()
    total_employees = Employee.query.filter_by(company_id=company_id).count()
    
    # Calculate this month's revenue
    this_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_revenue = db.session.query(func.sum(Sale.total_amount)).filter(
        Sale.company_id == company_id,
        Sale.date_created >= this_month_start
    ).scalar() or 0
    
    return {
        'total_users': total_users,
        'total_products': total_products,
        'total_sales': total_sales,
        'total_employees': total_employees,
        'monthly_revenue': float(monthly_revenue)
    }

def get_user_activity_analytics(company_id):
    """Get user activity analytics"""
    # This would be implemented based on your analytics session tracking
    # For now, returning mock data
    return {
        'active_sessions': 15,
        'daily_logins': 45,
        'avg_session_duration': 25.5,
        'most_used_modules': [
            {'name': 'Sales', 'usage': 85},
            {'name': 'Inventory', 'usage': 72},
            {'name': 'Finance', 'usage': 58}
        ]
    }
