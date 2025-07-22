"""
Workflow & Process Automation Routes
Provides endpoints for workflow management, business process automation, and approval workflows
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from extensions import db
from models.workflow_automation import (
    WorkflowTemplate, Workflow, WorkflowTask, WorkflowAction, WorkflowLog,
    ApprovalWorkflow, ProcessAutomation, AutomationExecution,
    WorkflowStatus, TaskStatus, TaskType
)
from models.user import User
from models.company import Company
import json

# Create blueprint
workflow_bp = Blueprint('workflow', __name__, url_prefix='/workflow')

@workflow_bp.route('/')
@login_required
def workflow_dashboard():
    """Main workflow dashboard"""
    try:
        company_id = current_user.company_id
        
        # Get workflow statistics
        total_workflows = Workflow.query.filter_by(company_id=company_id).count()
        active_workflows = Workflow.query.filter_by(
            company_id=company_id, 
            status=WorkflowStatus.ACTIVE
        ).count()
        
        # Get pending tasks for current user
        pending_tasks = WorkflowTask.query.join(Workflow).filter(
            and_(
                Workflow.company_id == company_id,
                WorkflowTask.assigned_to == current_user.id,
                WorkflowTask.status == TaskStatus.PENDING
            )
        ).limit(10).all()
        
        # Get recent workflow activity
        recent_workflows = Workflow.query.filter_by(company_id=company_id)\
                                        .order_by(Workflow.updated_at.desc())\
                                        .limit(5).all()
        
        # Get automation statistics
        active_automations = ProcessAutomation.query.filter_by(
            company_id=company_id, 
            is_active=True
        ).count()
        
        return render_template('workflow/dashboard.html',
                             total_workflows=total_workflows,
                             active_workflows=active_workflows,
                             pending_tasks=pending_tasks,
                             recent_workflows=recent_workflows,
                             active_automations=active_automations)
    
    except Exception as e:
        flash(f'Error loading workflow dashboard: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@workflow_bp.route('/templates')
@login_required
def workflow_templates():
    """List workflow templates"""
    try:
        company_id = current_user.company_id
        templates = WorkflowTemplate.query.filter_by(company_id=company_id)\
                                         .order_by(WorkflowTemplate.name).all()
        
        return render_template('workflow/templates.html', templates=templates)
    
    except Exception as e:
        flash(f'Error loading workflow templates: {str(e)}', 'error')
        return redirect(url_for('workflow.workflow_dashboard'))

@workflow_bp.route('/templates/create', methods=['GET', 'POST'])
@login_required
def create_template():
    """Create new workflow template"""
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form
            
            template = WorkflowTemplate(
                company_id=current_user.company_id,
                name=data.get('name'),
                description=data.get('description'),
                category=data.get('category'),
                template_config=json.loads(data.get('template_config', '{}')),
                default_settings=json.loads(data.get('default_settings', '{}')),
                requires_approval=data.get('requires_approval', False),
                auto_start=data.get('auto_start', False),
                created_by=current_user.id
            )
            
            db.session.add(template)
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Workflow template created successfully',
                    'template': template.to_dict()
                })
            else:
                flash('Workflow template created successfully', 'success')
                return redirect(url_for('workflow.workflow_templates'))
        
        except Exception as e:
            db.session.rollback()
            if request.is_json:
                return jsonify({'success': False, 'error': str(e)}), 400
            else:
                flash(f'Error creating template: {str(e)}', 'error')
    
    return render_template('workflow/create_template.html')

@workflow_bp.route('/workflows')
@login_required
def workflow_list():
    """List workflows"""
    try:
        company_id = current_user.company_id
        page = request.args.get('page', 1, type=int)
        status_filter = request.args.get('status')
        
        query = Workflow.query.filter_by(company_id=company_id)
        
        if status_filter:
            query = query.filter_by(status=WorkflowStatus(status_filter))
        
        workflows = query.order_by(Workflow.updated_at.desc())\
                        .paginate(page=page, per_page=20, error_out=False)
        
        return render_template('workflow/workflows.html', 
                             workflows=workflows,
                             status_filter=status_filter)
    
    except Exception as e:
        flash(f'Error loading workflows: {str(e)}', 'error')
        return redirect(url_for('workflow.workflow_dashboard'))

@workflow_bp.route('/workflows/create', methods=['GET', 'POST'])
@login_required
def create_workflow():
    """Create new workflow"""
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form
            
            workflow = Workflow(
                company_id=current_user.company_id,
                template_id=data.get('template_id'),
                name=data.get('name'),
                description=data.get('description'),
                workflow_type=data.get('workflow_type'),
                due_date=datetime.fromisoformat(data.get('due_date')) if data.get('due_date') else None,
                estimated_duration=data.get('estimated_duration', type=int),
                workflow_data=json.loads(data.get('workflow_data', '{}')),
                initiated_by=current_user.id,
                assigned_to=data.get('assigned_to', type=int)
            )
            
            db.session.add(workflow)
            db.session.flush()  # Get the workflow ID
            
            # Create workflow tasks if template is provided
            if workflow.template_id:
                template = WorkflowTemplate.query.get(workflow.template_id)
                if template and template.template_config:
                    create_workflow_tasks_from_template(workflow, template)
            
            # Log workflow creation
            log_entry = WorkflowLog(
                workflow_id=workflow.id,
                event_type='workflow_created',
                event_description=f'Workflow "{workflow.name}" created',
                user_id=current_user.id
            )
            db.session.add(log_entry)
            
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Workflow created successfully',
                    'workflow': workflow.to_dict()
                })
            else:
                flash('Workflow created successfully', 'success')
                return redirect(url_for('workflow.view_workflow', workflow_id=workflow.id))
        
        except Exception as e:
            db.session.rollback()
            if request.is_json:
                return jsonify({'success': False, 'error': str(e)}), 400
            else:
                flash(f'Error creating workflow: {str(e)}', 'error')
    
    # Get templates for the form
    templates = WorkflowTemplate.query.filter_by(
        company_id=current_user.company_id,
        is_active=True
    ).all()
    
    users = User.query.filter_by(company_id=current_user.company_id).all()
    
    return render_template('workflow/create_workflow.html', 
                         templates=templates, users=users)

@workflow_bp.route('/workflows/<int:workflow_id>')
@login_required
def view_workflow(workflow_id):
    """View workflow details"""
    try:
        workflow = Workflow.query.filter_by(
            id=workflow_id,
            company_id=current_user.company_id
        ).first_or_404()
        
        # Get workflow tasks
        tasks = WorkflowTask.query.filter_by(workflow_id=workflow_id)\
                                .order_by(WorkflowTask.step_number).all()
        
        # Get workflow logs
        logs = WorkflowLog.query.filter_by(workflow_id=workflow_id)\
                               .order_by(WorkflowLog.timestamp.desc()).all()
        
        # Update progress
        workflow.progress_percentage = workflow.calculate_progress()
        db.session.commit()
        
        return render_template('workflow/view_workflow.html',
                             workflow=workflow,
                             tasks=tasks,
                             logs=logs)
    
    except Exception as e:
        flash(f'Error loading workflow: {str(e)}', 'error')
        return redirect(url_for('workflow.workflow_list'))

@workflow_bp.route('/workflows/<int:workflow_id>/start', methods=['POST'])
@login_required
def start_workflow(workflow_id):
    """Start a workflow"""
    try:
        workflow = Workflow.query.filter_by(
            id=workflow_id,
            company_id=current_user.company_id
        ).first_or_404()
        
        if workflow.status != WorkflowStatus.DRAFT:
            return jsonify({'success': False, 'error': 'Workflow already started'}), 400
        
        workflow.status = WorkflowStatus.ACTIVE
        workflow.started_at = datetime.utcnow()
        
        # Start first pending task
        first_task = WorkflowTask.query.filter_by(
            workflow_id=workflow_id,
            step_number=1
        ).first()
        
        if first_task:
            first_task.status = TaskStatus.IN_PROGRESS
            first_task.started_at = datetime.utcnow()
        
        # Log workflow start
        log_entry = WorkflowLog(
            workflow_id=workflow.id,
            event_type='workflow_started',
            event_description=f'Workflow started by {current_user.full_name}',
            user_id=current_user.id
        )
        db.session.add(log_entry)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Workflow started successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@workflow_bp.route('/tasks')
@login_required
def my_tasks():
    """List user's workflow tasks"""
    try:
        page = request.args.get('page', 1, type=int)
        status_filter = request.args.get('status')
        
        query = WorkflowTask.query.join(Workflow).filter(
            and_(
                Workflow.company_id == current_user.company_id,
                WorkflowTask.assigned_to == current_user.id
            )
        )
        
        if status_filter:
            query = query.filter(WorkflowTask.status == TaskStatus(status_filter))
        
        tasks = query.order_by(WorkflowTask.due_date.asc())\
                    .paginate(page=page, per_page=20, error_out=False)
        
        return render_template('workflow/my_tasks.html', 
                             tasks=tasks,
                             status_filter=status_filter)
    
    except Exception as e:
        flash(f'Error loading tasks: {str(e)}', 'error')
        return redirect(url_for('workflow.workflow_dashboard'))

@workflow_bp.route('/tasks/<int:task_id>')
@login_required
def view_task(task_id):
    """View task details"""
    try:
        task = WorkflowTask.query.join(Workflow).filter(
            and_(
                WorkflowTask.id == task_id,
                Workflow.company_id == current_user.company_id
            )
        ).first_or_404()
        
        # Get task actions
        actions = WorkflowAction.query.filter_by(task_id=task_id)\
                                    .order_by(WorkflowAction.performed_at.desc()).all()
        
        return render_template('workflow/view_task.html',
                             task=task,
                             actions=actions)
    
    except Exception as e:
        flash(f'Error loading task: {str(e)}', 'error')
        return redirect(url_for('workflow.my_tasks'))

@workflow_bp.route('/tasks/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    """Complete a workflow task"""
    try:
        task = WorkflowTask.query.join(Workflow).filter(
            and_(
                WorkflowTask.id == task_id,
                Workflow.company_id == current_user.company_id,
                WorkflowTask.assigned_to == current_user.id
            )
        ).first_or_404()
        
        data = request.get_json() if request.is_json else request.form
        
        # Update task status
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.result_data = json.loads(data.get('result_data', '{}'))
        
        # Create action record
        action = WorkflowAction(
            task_id=task.id,
            action_type='complete',
            action_data=task.result_data,
            comments=data.get('comments'),
            performed_by=current_user.id
        )
        db.session.add(action)
        
        # Log task completion
        log_entry = WorkflowLog(
            workflow_id=task.workflow_id,
            event_type='task_completed',
            event_description=f'Task "{task.name}" completed by {current_user.full_name}',
            user_id=current_user.id,
            task_id=task.id
        )
        db.session.add(log_entry)
        
        # Check if workflow is complete
        workflow = task.workflow
        workflow.progress_percentage = workflow.calculate_progress()
        
        if workflow.progress_percentage >= 100:
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.utcnow()
        
        # Start next task if available
        next_task = WorkflowTask.query.filter_by(
            workflow_id=task.workflow_id,
            step_number=task.step_number + 1,
            status=TaskStatus.PENDING
        ).first()
        
        if next_task:
            next_task.status = TaskStatus.IN_PROGRESS
            next_task.started_at = datetime.utcnow()
        
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Task completed successfully'
            })
        else:
            flash('Task completed successfully', 'success')
            return redirect(url_for('workflow.my_tasks'))
    
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        else:
            flash(f'Error completing task: {str(e)}', 'error')
            return redirect(url_for('workflow.view_task', task_id=task_id))

@workflow_bp.route('/approvals')
@login_required
def approval_workflows():
    """List approval workflows"""
    try:
        company_id = current_user.company_id
        approvals = ApprovalWorkflow.query.filter_by(company_id=company_id)\
                                         .order_by(ApprovalWorkflow.name).all()
        
        return render_template('workflow/approvals.html', approvals=approvals)
    
    except Exception as e:
        flash(f'Error loading approval workflows: {str(e)}', 'error')
        return redirect(url_for('workflow.workflow_dashboard'))

@workflow_bp.route('/automations')
@login_required
def process_automations():
    """List process automations"""
    try:
        company_id = current_user.company_id
        automations = ProcessAutomation.query.filter_by(company_id=company_id)\
                                            .order_by(ProcessAutomation.name).all()
        
        return render_template('workflow/automations.html', automations=automations)
    
    except Exception as e:
        flash(f'Error loading process automations: {str(e)}', 'error')
        return redirect(url_for('workflow.workflow_dashboard'))

@workflow_bp.route('/api/workflow-stats')
@login_required
def workflow_stats_api():
    """API endpoint for workflow statistics"""
    try:
        company_id = current_user.company_id
        
        # Workflow status distribution
        status_stats = db.session.query(
            Workflow.status,
            func.count(Workflow.id)
        ).filter_by(company_id=company_id).group_by(Workflow.status).all()
        
        # Task status distribution
        task_stats = db.session.query(
            WorkflowTask.status,
            func.count(WorkflowTask.id)
        ).join(Workflow).filter(Workflow.company_id == company_id)\
         .group_by(WorkflowTask.status).all()
        
        # Weekly workflow activity
        week_ago = datetime.utcnow() - timedelta(days=7)
        weekly_activity = db.session.query(
            func.date(Workflow.created_at),
            func.count(Workflow.id)
        ).filter(
            and_(
                Workflow.company_id == company_id,
                Workflow.created_at >= week_ago
            )
        ).group_by(func.date(Workflow.created_at)).all()
        
        return jsonify({
            'status_distribution': [
                {'status': status.value if status else 'unknown', 'count': count}
                for status, count in status_stats
            ],
            'task_distribution': [
                {'status': status.value if status else 'unknown', 'count': count}
                for status, count in task_stats
            ],
            'weekly_activity': [
                {'date': date.isoformat() if date else None, 'count': count}
                for date, count in weekly_activity
            ]
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def create_workflow_tasks_from_template(workflow, template):
    """Create workflow tasks from template configuration"""
    try:
        config = template.template_config or {}
        tasks_config = config.get('tasks', [])
        
        for i, task_config in enumerate(tasks_config, 1):
            task = WorkflowTask(
                workflow_id=workflow.id,
                name=task_config.get('name', f'Task {i}'),
                description=task_config.get('description'),
                task_type=TaskType(task_config.get('type', 'manual')),
                step_number=i,
                priority=task_config.get('priority', 'medium'),
                estimated_duration=task_config.get('estimated_duration'),
                task_config=task_config,
                auto_assign=task_config.get('auto_assign', False),
                auto_complete=task_config.get('auto_complete', False)
            )
            
            # Set due date if specified
            if task_config.get('due_in_days'):
                task.due_date = datetime.utcnow() + timedelta(days=task_config['due_in_days'])
            
            # Auto-assign if configured
            if task.auto_assign and task_config.get('assigned_role'):
                user = User.query.filter_by(
                    company_id=workflow.company_id,
                    role=task_config['assigned_role']
                ).first()
                if user:
                    task.assigned_to = user.id
            
            db.session.add(task)
    
    except Exception as e:
        current_app.logger.error(f"Error creating tasks from template: {str(e)}")
        raise e
