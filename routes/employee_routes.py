from flask import Blueprint, jsonify, request
from database.models import Employee, Notification, db
from services.reassignment_service import ReassignmentService
from datetime import datetime, timezone

employee_bp = Blueprint("employees", __name__, url_prefix="/api")

@employee_bp.route("/employees", methods=["GET"])
def get_employees():
    """Returns all 8 employees with skills, workload, and availability status."""
    employees = Employee.query.order_by(Employee.employee_code.asc()).all()
    return jsonify({
        "status": "success",
        "count": len(employees),
        "employees": [e.to_dict(include_skills=True) for e in employees]
    }), 200

@employee_bp.route("/employees/<int:emp_id>", methods=["GET"])
def get_employee(emp_id):
    """Returns a single employee by ID."""
    emp = db.session.get(Employee, emp_id)
    if not emp:
        return jsonify({"status": "error", "message": "Employee not found"}), 404
    return jsonify({"status": "success", "employee": emp.to_dict(include_skills=True)}), 200

@employee_bp.route("/attendance/absent", methods=["POST"])
def mark_absent():
    """
    Marks an employee absent and triggers immediate reassignment analysis.
    Supports either {"employee_id": "E003"} or {"employee_id": 3}.
    """
    data = request.get_json() or {}
    emp_param = data.get("employee_id")

    if not emp_param:
        return jsonify({"status": "error", "message": "employee_id is required"}), 400

    employee = None
    if isinstance(emp_param, int) or (isinstance(emp_param, str) and emp_param.isdigit()):
        employee = db.session.get(Employee, int(emp_param))
    elif isinstance(emp_param, str):
        employee = Employee.query.filter_by(employee_code=emp_param.strip().upper()).first()
        if not employee:
            employee = Employee.query.filter_by(name=emp_param.strip().upper()).first()

    if not employee:
        return jsonify({"status": "error", "message": f"Employee '{emp_param}' not found"}), 404

    # Update availability to Absent
    employee.availability_status = "Absent"
    
    # Create notification for absence
    absence_notif = Notification(
        employee_id=employee.id,
        message=f"Employee {employee.name} ({employee.employee_code}) was marked ABSENT.",
        notification_type="ABSENCE",
        status="UNREAD",
        created_at=datetime.now(timezone.utc)
    )
    db.session.add(absence_notif)
    db.session.commit()

    # Automatically run reassignment analysis
    analysis_result = ReassignmentService.analyze_reassignment(employee.id)

    return jsonify({
        "status": "success",
        "message": f"Employee {employee.name} marked ABSENT.",
        "employee": employee.to_dict(),
        "analysis": analysis_result
    }), 200

@employee_bp.route("/attendance/available", methods=["POST"])
def mark_available():
    """Marks an employee Available (useful for testing/resetting status)."""
    data = request.get_json() or {}
    emp_param = data.get("employee_id")

    if not emp_param:
        return jsonify({"status": "error", "message": "employee_id is required"}), 400

    employee = None
    if isinstance(emp_param, int) or (isinstance(emp_param, str) and emp_param.isdigit()):
        employee = Employee.query.get(int(emp_param))
    elif isinstance(emp_param, str):
        employee = Employee.query.filter_by(employee_code=emp_param.strip().upper()).first()
        if not employee:
            employee = Employee.query.filter_by(name=emp_param.strip().upper()).first()

    if not employee:
        return jsonify({"status": "error", "message": f"Employee '{emp_param}' not found"}), 404

    employee.availability_status = "Available"
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": f"Employee {employee.name} marked AVAILABLE.",
        "employee": employee.to_dict()
    }), 200
