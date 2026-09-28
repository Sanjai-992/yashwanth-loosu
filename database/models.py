from datetime import datetime, timezone
from .database import db

def utc_now():
    return datetime.now(timezone.utc)

class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), unique=True, nullable=False)        # A, B, C, D, E, F, G, H, I
    rfid_key = db.Column(db.String(10), unique=True, nullable=False)    # A, B, C, D, E, F, G, H, I
    skill = db.Column(db.String(100), nullable=False)                   # Web Development, Database, Python, Testing, etc.
    workload = db.Column(db.Integer, nullable=False, default=30)        # 0 - 100 percentage
    status = db.Column(db.String(30), nullable=False, default="Available") # Available, Busy
    attendance_status = db.Column(db.String(30), nullable=False, default="Waiting for Attendance") # Waiting for Attendance, Present, Absent
    attendance_time = db.Column(db.String(30), nullable=True)

    # Relationships
    assigned_tasks = db.relationship("Task", backref="assigned_worker", lazy=True, foreign_keys="Task.assigned_employee")

    def to_dict(self):
        tasks = [t.to_dict() for t in self.assigned_tasks]
        primary_task = tasks[0]["task_name"] if tasks else "None"
        return {
            "id": self.id,
            "name": self.name,
            "rfid_key": self.rfid_key,
            "skill": self.skill,
            "workload": self.workload,
            "status": self.status,
            "attendance_status": self.attendance_status,
            "attendance_time": self.attendance_time,
            "current_task": primary_task,
            "tasks": tasks
        }


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(150), nullable=False)
    required_skill = db.Column(db.String(100), nullable=False)
    assigned_employee = db.Column(db.String(10), db.ForeignKey("employees.name"), nullable=True)
    original_employee = db.Column(db.String(10), nullable=True)
    status = db.Column(db.String(30), nullable=False, default="Active") # Active, Reassigned, Completed

    def to_dict(self):
        return {
            "id": self.id,
            "task_name": self.task_name,
            "required_skill": self.required_skill,
            "assigned_employee": self.assigned_employee,
            "original_employee": self.original_employee,
            "status": self.status
        }


class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    employee_name = db.Column(db.String(10), nullable=False)
    date = db.Column(db.String(30), nullable=False)
    time = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(30), nullable=False) # Present, Absent

    def to_dict(self):
        return {
            "id": self.id,
            "employee_name": self.employee_name,
            "date": self.date,
            "time": self.time,
            "status": self.status
        }


class Reassignment(db.Model):
    __tablename__ = "reassignments"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    task_name = db.Column(db.String(150), nullable=False)
    required_skill = db.Column(db.String(100), nullable=False)
    absent_employee = db.Column(db.String(10), nullable=False)
    new_employee = db.Column(db.String(10), nullable=False)
    workload_before = db.Column(db.Integer, nullable=True)
    workload_after = db.Column(db.Integer, nullable=True)
    reason = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=utc_now)
    email_sent = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "required_skill": self.required_skill,
            "absent_employee": self.absent_employee,
            "new_employee": self.new_employee,
            "workload_before": self.workload_before,
            "workload_after": self.workload_after,
            "reason": self.reason,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else "",
            "email_sent": self.email_sent
        }
