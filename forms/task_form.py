from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, SubmitField
from wtforms.validators import DataRequired, Optional

class TaskForm(FlaskForm):
    title = StringField("Task Title", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Optional()])
    due_date = DateTimeField("Due Date (YYYY-MM-DD HH:MM)", format='%Y-%m-%d %H:%M', validators=[Optional()])
    status = SelectField("Status", choices=[
        ("Pending", "Pending"),
        ("Completed", "Completed"),
        ("Overdue", "Overdue")
    ], default="Pending")

    priority = SelectField("Priority", choices=[
        ("Low", "Low"),
        ("Normal", "Normal"),
        ("High", "High")
    ], default="Normal")

    related_to = StringField("Related To (e.g., Lead, Deal, Contact)", validators=[Optional()])
    submit = SubmitField("Save Task")
