from flask import Blueprint, jsonify, request
from database.models import Employee, Task, Attendance, Reassignment
from database.database import db
from database.seed import run_seed
from services.reassignment_service import ReassignmentService

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/dashboard", methods=["GET"])
def get_dashboard():
    """Returns top-level metric counters."""
    total = Employee.query.count()
    present = Employee.query.filter_by(attendance_status="PRESENT").count()
    absent = Employee.query.filter_by(attendance_status="ABSENT").count()
    reassigned = Reassignment.query.count()
    
    return jsonify({
        "status": "success",
        "metrics": {
            "total": total,
            "present": present,
            "absent": absent,
            "reassigned": reassigned
        }
    }), 200

@api_bp.route("/employees", methods=["GET"])
def get_employees():
    """Returns all 9 employees."""
    employees = Employee.query.order_by(Employee.name.asc()).all()
    return jsonify({
        "status": "success",
        "count": len(employees),
        "employees": [e.to_dict() for e in employees]
    }), 200

@api_bp.route("/tasks", methods=["GET"])
def get_tasks():
    """Returns all tasks."""
    tasks = Task.query.order_by(Task.id.asc()).all()
    return jsonify({
        "status": "success",
        "count": len(tasks),
        "tasks": [t.to_dict() for t in tasks]
    }), 200

@api_bp.route("/attendance", methods=["POST"])
def record_attendance():
    """Records attendance for an employee when key is pressed."""
    data = request.get_json() or {}
    key = data.get("key") or data.get("employee_name") or data.get("rfid_key")
    
    if not key:
        return jsonify({"status": "error", "message": "Key or employee_name parameter is required"}), 400

    try:
        result = ReassignmentService.mark_attendance(key)
        return jsonify(result), 200
    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route("/attendance/end", methods=["POST"])
def end_attendance():
    """Marks unmarked employees ABSENT and triggers automatic task reassignment."""
    try:
        result = ReassignmentService.end_attendance_and_reassign()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route("/send-email", methods=["POST"])
def send_email():
    """Simulates sending the assignment email."""
    data = request.get_json() or {}
    reassign_id = data.get("reassignment_id")

    if not reassign_id:
        return jsonify({"status": "error", "message": "reassignment_id is required"}), 400

    try:
        result = ReassignmentService.send_task_email(int(reassign_id))
        return jsonify(result), 200
    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route("/reassign-task", methods=["POST"])
def manual_reassign():
    """Allows manual override or targeted reassignment."""
    data = request.get_json() or {}
    task_id = data.get("task_id")
    new_employee = data.get("new_employee")
    
    if not task_id or not new_employee:
        return jsonify({"status": "error", "message": "task_id and new_employee are required"}), 400

    task = db.session.get(Task, int(task_id))
    emp = Employee.query.filter_by(name=new_employee.upper()).first()
    
    if not task or not emp:
        return jsonify({"status": "error", "message": "Task or employee not found"}), 404

    old_emp = task.assigned_employee
    task.assigned_employee = emp.name
    task.status = "Reassigned"
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": f"Task {task.task_name} reassigned to Employee {emp.name}",
        "task": task.to_dict()
    }), 200

@api_bp.route("/reset", methods=["POST"])
def reset_system():
    """Resets system back to initial demo state."""
    try:
        run_seed()
        return jsonify({
            "status": "success",
            "message": "System reset to initial state (All 9 employees waiting for attendance)."
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
