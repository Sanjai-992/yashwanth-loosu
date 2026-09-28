from flask import Blueprint, jsonify, request
from database.models import Employee, ReassignmentHistory
from services.reassignment_service import ReassignmentService

reassignment_bp = Blueprint("reassignments", __name__, url_prefix="/api/reassignment")

@reassignment_bp.route("/analyze", methods=["POST"])
def analyze():
    """
    Analyzes task reassignment for a given employee.
    Request body: {"employee_id": "E003"} or {"employee_id": 3} or {"employee_id": "C"}
    """
    data = request.get_json() or {}
    emp_param = data.get("employee_id")

    if not emp_param:
        return jsonify({"status": "error", "message": "employee_id is required"}), 400

    employee = None
    if isinstance(emp_param, int) or (isinstance(emp_param, str) and emp_param.isdigit()):
        from database.database import db
        employee = db.session.get(Employee, int(emp_param))
    elif isinstance(emp_param, str):
        employee = Employee.query.filter_by(employee_code=emp_param.strip().upper()).first()
        if not employee:
            employee = Employee.query.filter_by(name=emp_param.strip().upper()).first()

    if not employee:
        return jsonify({"status": "error", "message": f"Employee '{emp_param}' not found"}), 404

    try:
        result = ReassignmentService.analyze_reassignment(employee.id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@reassignment_bp.route("/history", methods=["GET"])
def get_history():
    """Returns past reassignment recommendations and their approval status."""
    history_records = ReassignmentHistory.query.order_by(ReassignmentHistory.created_at.desc()).all()
    return jsonify({
        "status": "success",
        "count": len(history_records),
        "history": [h.to_dict() for h in history_records]
    }), 200

@reassignment_bp.route("/<int:history_id>", methods=["GET"])
def get_reassignment(history_id):
    """Returns a specific reassignment analysis record."""
    from database.database import db
    history = db.session.get(ReassignmentHistory, history_id)
    if not history:
        return jsonify({"status": "error", "message": "Reassignment record not found"}), 404
    return jsonify({"status": "success", "reassignment": history.to_dict()}), 200

@reassignment_bp.route("/<int:history_id>/approve", methods=["POST"])
def approve_by_id(history_id):
    """Supervisor approves a reassignment recommendation."""
    try:
        result = ReassignmentService.approve_reassignment(history_id)
        return jsonify(result), 200
    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@reassignment_bp.route("/<int:history_id>/reject", methods=["POST"])
def reject_by_id(history_id):
    """Supervisor rejects a reassignment recommendation."""
    try:
        result = ReassignmentService.reject_reassignment(history_id)
        return jsonify(result), 200
    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
