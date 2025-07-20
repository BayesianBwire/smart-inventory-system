from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired
from models.employee import Employee  # if needed for dynamic choices

class SupportTicketForm(FlaskForm):
    subject = StringField("Subject", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    priority = SelectField("Priority", choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')])
    category = SelectField("Category", choices=[('Technical', 'Technical'), ('HR', 'HR'), ('Payroll', 'Payroll'), ('Other', 'Other')])
    status = SelectField("Status", choices=[('Open', 'Open'), ('In Progress', 'In Progress'), ('Closed', 'Closed')])
    assigned_staff_id = SelectField("Assign To (Optional)", coerce=int, choices=[], validate_choice=False)
    submit = SubmitField("Submit Ticket")
