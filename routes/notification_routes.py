from flask import Blueprint, jsonify
from database.models import Notification, db

notification_bp = Blueprint("notifications", __name__, url_prefix="/api")

@notification_bp.route("/notifications", methods=["GET"])
def get_notifications():
    """Returns recent system and reassignment notifications."""
    notifs = Notification.query.order_by(Notification.created_at.desc()).limit(50).all()
    unread_count = Notification.query.filter_by(status="UNREAD").count()
    return jsonify({
        "status": "success",
        "count": len(notifs),
        "unread_count": unread_count,
        "notifications": [n.to_dict() for n in notifs]
    }), 200

@notification_bp.route("/notifications/<int:notif_id>/read", methods=["POST"])
def mark_read(notif_id):
    """Marks a single notification as read."""
    notif = db.session.get(Notification, notif_id)
    if not notif:
        return jsonify({"status": "error", "message": "Notification not found"}), 404
    notif.status = "READ"
    db.session.commit()
    return jsonify({"status": "success", "notification": notif.to_dict()}), 200

@notification_bp.route("/notifications/read-all", methods=["POST"])
def mark_all_read():
    """Marks all notifications as read."""
    Notification.query.filter_by(status="UNREAD").update({"status": "READ"})
    db.session.commit()
    return jsonify({"status": "success", "message": "All notifications marked as read."}), 200
