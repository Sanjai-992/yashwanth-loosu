from flask import Blueprint, jsonify
from database.models import Task
from database.database import db

task_bp = Blueprint("tasks", __name__, url_prefix="/api")

@task_bp.route("/tasks", methods=["GET"])
def get_tasks():
    """Returns all tasks in the system with their assigned employee info."""
    tasks = Task.query.order_by(Task.task_code.asc()).all()
    return jsonify({
        "status": "success",
        "count": len(tasks),
        "tasks": [t.to_dict() for t in tasks]
    }), 200

@task_bp.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    """Returns details for a single task."""
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({"status": "error", "message": "Task not found"}), 404
    return jsonify({"status": "success", "task": task.to_dict()}), 200
