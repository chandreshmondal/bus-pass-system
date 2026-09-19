from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from models import db, PassApplication, BusRoute

admin_bp = Blueprint("admin_bp", __name__)


def _require_admin():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"success": False, "message": "Admin access required."}), 403
    return None


@admin_bp.route("/applications", methods=["GET"])
@jwt_required()
def list_applications():
    denied = _require_admin()
    if denied:
        return denied

    status_filter = request.args.get("status")
    query = PassApplication.query
    if status_filter:
        query = query.filter_by(status=status_filter)

    apps = query.order_by(PassApplication.applied_on.desc()).all()
    return jsonify({"success": True, "applications": [a.to_dict() for a in apps]}), 200


@admin_bp.route("/applications/<int:application_id>/approve", methods=["PUT"])
@jwt_required()
def approve_application(application_id):
    denied = _require_admin()
    if denied:
        return denied

    application = PassApplication.query.get(application_id)
    if not application:
        return jsonify({"success": False, "message": "Application not found."}), 404

    if application.status != "pending":
        return jsonify({"success": False, "message": f"Cannot approve — status is '{application.status}'."}), 400

    application.status = "approved"
    application.reviewed_on = datetime.utcnow()
    db.session.commit()

    return