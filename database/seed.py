import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask
from config import Config
from database.database import db
from database.models import Employee, Task, Attendance, Reassignment

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def run_seed():
    print("Initializing SQLite database with 9 employees & assigned tasks...")
    db.session.remove()
    db.drop_all()
    db.create_all()

    # Exactly 9 employees: A, B, C, D, E, F, G, H, I
    employees_data = [
        {"name": "A", "key": "A", "skill": "Web Development", "workload": 30, "status": "Available", "task": "Web Portal Setup"},
        {"name": "B", "key": "B", "skill": "Database",        "workload": 80, "status": "Busy",      "task": "Database Module"},
        {"name": "C", "key": "C", "skill": "Python",          "workload": 40, "status": "Available", "task": "API Integration"},
        {"name": "D", "key": "D", "skill": "Testing",         "workload": 60, "status": "Available", "task": "QA Automation"},
        {"name": "E", "key": "E", "skill": "Frontend",        "workload": 25, "status": "Available", "task": "UI Dashboard"},
        {"name": "F", "key": "F", "skill": "Backend",         "workload": 90, "status": "Busy",      "task": "Microservices Auth"},
        {"name": "G", "key": "G", "skill": "Database",        "workload": 35, "status": "Available", "task": "DB Optimization"},
        {"name": "H", "key": "H", "skill": "Testing",         "workload": 50, "status": "Available", "task": "Load Testing"},
        {"name": "I", "key": "I", "skill": "Web Development", "workload": 20, "status": "Available", "task": "Landing Page"},
    ]

    for emp_info in employees_data:
        emp = Employee(
            name=emp_info["name"],
            rfid_key=emp_info["key"],
            skill=emp_info["skill"],
            workload=emp_info["workload"],
            status=emp_info["status"],
            attendance_status="Waiting for Attendance",
            attendance_time=None
        )
        db.session.add(emp)

    db.session.flush()

    # Seed initial tasks assigned to employees
    for emp_info in employees_data:
        task = Task(
            task_name=emp_info["task"],
            required_skill=emp_info["skill"],
            assigned_employee=emp_info["name"],
            original_employee=emp_info["name"],
            status="Active"
        )
        db.session.add(task)

    db.session.commit()
    print("Database successfully seeded with 9 employees & tasks in 'Waiting for Attendance' state!")

def seed_database(app=None):
    if app:
        with app.app_context():
            run_seed()
    else:
        app = create_app()
        with app.app_context():
            run_seed()

if __name__ == "__main__":
    seed_database()
