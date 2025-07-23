"""
Advanced Workflow & Process Automation Models
Provides workflow management, business process automation, and approval workflows
"""

from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Float, Enum
from sqlalchemy.orm import relationship
from extensions import db
import enum

class WorkflowStatus(enum.Enum):
    """Workflow execution status"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskStatus(enum.Enum):
    """Individual task status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"

class TaskType(enum.Enum):
    """Types of workflow tasks"""
    APPROVAL = "approval"
    REVIEW = "review"
    DATA_ENTRY = "data_entry"
    NOTIFICATION = "notification"
    AUTOMATED = "automated"
    CONDITIONAL = "conditional"

class WorkflowTemplate(db.Model):
    """Template for creating reusable workflows"""
    __tablename__ = 'workflow_templates'
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    
    # Template Details
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))  # e.g., 'HR', 'Finance', 'Procurement'
    version = Column(String(20), default='1.0')
    
    # Template Configuration
    template_config = Column(JSON)  # Workflow structure and rules
    default_settings = Column(JSON)  # Default values for new workflows
    
    # Template Properties
    is_active = Column(Boolean, default=True)
    requires_approval = Column(Boolean, default=False)
    auto_start = Column(Boolean, default=False)
    
    # Metadata
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship('Company', backref='workflow_templates')
    creator = relationship('User', backref='created_workflow_templates')
    workflows = relationship('Workflow', backref='template')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'version': self.version,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Workflow(db.Model):
    """Active workflow instance"""
    __tablename__ = 'workflows'
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    template_id = Column(Integer, ForeignKey('workflow_templates.id'))
    
    # Workflow Identity
    name = Column(String(200), nullable=False)
    description = Column(Text)
    workflow_type = Column(String(100))  # e.g., 'expense_approval', 'hr_onboarding'
    
    # Workflow State
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.DRAFT)
    current_step = Column(Integer, default=0)
    progress_percentage = Column(Float, default=0.0)
    
    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    due_date = Column(DateTime)
    estimated_duration = Column(Integer)  # in minutes
    
    # Configuration
    workflow_data = Column(JSON)  # Dynamic data for the workflow
    settings = Column(JSON)  # Workflow-specific settings
    
    # Ownership
    initiated_by = Column(Integer, ForeignKey('users.id'))
    assigned_to = Column(Integer, ForeignKey('users.id'))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship('Company', backref='workflows')
    initiator = relationship('User', foreign_keys=[initiated_by], backref='initiated_workflows')
    assignee = relationship('User', foreign_keys=[assigned_to], backref='assigned_workflows')
    tasks = relationship('WorkflowTask', backref='workflow', cascade='all, delete-orphan')
    logs = relationship('WorkflowLog', backref='workflow', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value if self.status else None,
            'current_step': self.current_step,
            'progress_percentage': self.progress_percentage,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'initiator': self.initiator.full_name if self.initiator else None,
            'assignee': self.assignee.full_name if self.assignee else None
        }
    
    def calculate_progress(self):
        """Calculate workflow progress based on completed tasks"""
        if not self.tasks:
            return 0.0
        
        completed_tasks = sum(1 for task in self.tasks if task.status == TaskStatus.COMPLETED)
        return (completed_tasks / len(self.tasks)) * 100

class WorkflowTask(db.Model):
    """Individual task within a workflow"""
    __tablename__ = 'workflow_tasks'
    
    id = Column(Integer, primary_key=True)
    workflow_id = Column(Integer, ForeignKey('workflows.id'), nullable=False)
    
    # Task Identity
    name = Column(String(200), nullable=False)
    description = Column(Text)
    task_type = Column(Enum(TaskType), nullable=False)
    step_number = Column(Integer, nullable=False)
    
    # Task State
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    priority = Column(String(20), default='medium')  # low, medium, high, urgent
    
    # Assignment
    assigned_to = Column(Integer, ForeignKey('users.id'))
    assigned_group = Column(String(100))  # Role or department
    
    # Timing
    due_date = Column(DateTime)
    estimated_duration = Column(Integer)  # in minutes
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Task Configuration
    task_config = Column(JSON)  # Task-specific configuration
    form_data = Column(JSON)  # Form fields and values
    result_data = Column(JSON)  # Task execution results
    
    # Dependencies
    depends_on_tasks = Column(JSON)  # List of task IDs this depends on
    blocks_tasks = Column(JSON)  # List of task IDs this blocks
    
    # Automation
    auto_assign = Column(Boolean, default=False)
    auto_complete = Column(Boolean, default=False)
    notification_enabled = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assignee = relationship('User', backref='workflow_tasks')
    actions = relationship('WorkflowAction', backref='task', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'task_type': self.task_type.value if self.task_type else None,
            'status': self.status.value if self.status else None,
            'priority': self.priority,
            'step_number': self.step_number,
            'assigned_to': self.assignee.full_name if self.assignee else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def is_overdue(self):
        """Check if task is overdue"""
        if self.due_date and self.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            return datetime.utcnow() > self.due_date
        return False

class WorkflowAction(db.Model):
    """Actions taken on workflow tasks"""
    __tablename__ = 'workflow_actions'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('workflow_tasks.id'), nullable=False)
    
    # Action Details
    action_type = Column(String(50), nullable=False)  # approve, reject, comment, complete, etc.
    action_data = Column(JSON)  # Action-specific data
    comments = Column(Text)
    
    # Action Metadata
    performed_by = Column(Integer, ForeignKey('users.id'))
    performed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', backref='workflow_actions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'action_type': self.action_type,
            'comments': self.comments,
            'performed_by': self.user.full_name if self.user else None,
            'performed_at': self.performed_at.isoformat() if self.performed_at else None
        }

class WorkflowLog(db.Model):
    """Audit log for workflow events"""
    __tablename__ = 'workflow_logs'
    
    id = Column(Integer, primary_key=True)
    workflow_id = Column(Integer, ForeignKey('workflows.id'), nullable=False)
    
    # Log Details
    event_type = Column(String(100), nullable=False)  # started, completed, failed, etc.
    event_description = Column(Text)
    event_data = Column(JSON)
    
    # Context
    user_id = Column(Integer, ForeignKey('users.id'))
    task_id = Column(Integer, ForeignKey('workflow_tasks.id'))
    
    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', backref='workflow_log_entries')
    task = relationship('WorkflowTask', backref='log_entries')
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'event_description': self.event_description,
            'user': self.user.full_name if self.user else None,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class ApprovalWorkflow(db.Model):
    """Specialized workflow for approval processes"""
    __tablename__ = 'approval_workflows'
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    
    # Approval Identity
    name = Column(String(200), nullable=False)
    description = Column(Text)
    approval_type = Column(String(100))  # expense, purchase_order, leave_request, etc.
    
    # Approval Rules
    approval_rules = Column(JSON)  # Rules for automatic routing
    approval_levels = Column(JSON)  # Multi-level approval configuration
    
    # Thresholds
    min_amount = Column(Float, default=0.0)
    max_amount = Column(Float)
    requires_documentation = Column(Boolean, default=False)
    
    # Workflow Integration
    workflow_template_id = Column(Integer, ForeignKey('workflow_templates.id'))
    
    # Settings
    is_active = Column(Boolean, default=True)
    auto_approve_threshold = Column(Float)  # Auto-approve below this amount
    escalation_timeout = Column(Integer, default=72)  # hours before escalation
    
    # Metadata
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship('Company', backref='approval_workflows')
    workflow_template = relationship('WorkflowTemplate', backref='approval_workflows')
    creator = relationship('User', backref='created_approval_workflows')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'approval_type': self.approval_type,
            'min_amount': self.min_amount,
            'max_amount': self.max_amount,
            'is_active': self.is_active,
            'auto_approve_threshold': self.auto_approve_threshold
        }

class ProcessAutomation(db.Model):
    """Automated business process configurations"""
    __tablename__ = 'process_automations'
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    
    # Automation Identity
    name = Column(String(200), nullable=False)
    description = Column(Text)
    automation_type = Column(String(100))  # scheduled, triggered, conditional
    
    # Trigger Configuration
    trigger_config = Column(JSON)  # What triggers this automation
    trigger_conditions = Column(JSON)  # Conditions that must be met
    
    # Action Configuration
    action_config = Column(JSON)  # What actions to perform
    action_parameters = Column(JSON)  # Parameters for actions
    
    # Scheduling (for scheduled automations)
    schedule_config = Column(JSON)  # Cron-like scheduling
    next_run = Column(DateTime)
    last_run = Column(DateTime)
    
    # State
    is_active = Column(Boolean, default=True)
    run_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    
    # Error Handling
    retry_config = Column(JSON)  # Retry configuration
    error_handling = Column(JSON)  # Error handling rules
    
    # Metadata
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship('Company', backref='process_automations')
    creator = relationship('User', backref='created_automations')
    executions = relationship('AutomationExecution', backref='automation', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'automation_type': self.automation_type,
            'is_active': self.is_active,
            'run_count': self.run_count,
            'success_rate': (self.success_count / self.run_count * 100) if self.run_count > 0 else 0,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'last_run': self.last_run.isoformat() if self.last_run else None
        }

class AutomationExecution(db.Model):
    """Log of automation executions"""
    __tablename__ = 'automation_executions'
    
    id = Column(Integer, primary_key=True)
    automation_id = Column(Integer, ForeignKey('process_automations.id'), nullable=False)
    
    # Execution Details
    execution_status = Column(String(50))  # success, failed, partial
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    duration = Column(Integer)  # in seconds
    
    # Execution Data
    input_data = Column(JSON)  # Input data for the execution
    output_data = Column(JSON)  # Results of the execution
    error_details = Column(JSON)  # Error information if failed
    
    # Context
    triggered_by = Column(String(100))  # What triggered this execution
    execution_context = Column(JSON)  # Additional context
    
    def to_dict(self):
        return {
            'id': self.id,
            'execution_status': self.execution_status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'triggered_by': self.triggered_by
        }
