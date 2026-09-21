from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from models import db, PassApplication, BusRoute, Notification

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

    notify = Notification(
        user_id=application.user_id,
        message=f"Your pass application (ID {application.id}) has been approved!"
    )
    db.session.add(notify)
    db.session.commit()

    return jsonify({"success": True, "application": application.to_dict()}), 200


@admin_bp.route("/applications/<int:application_id>/reject", methods=["PUT"])
@jwt_required()
def reject_application(application_id):
    denied = _require_admin()
    if denied:
        return denied

    application = PassApplication.query.get(application_id)
    if not application:
        return jsonify({"success": False, "message": "Application not found."}), 404

    if application.status != "pending":
        return jsonify({"success": False, "message": f"Cannot reject — status is '{application.status}'."}), 400

    # Single generic auto-generated reason - no admin input needed
    reason = "Rejected by admin after review."

    application.status = "rejected"
    application.rejection_reason = reason
    application.reviewed_on = datetime.utcnow()
    db.session.commit()

    notify = Notification(
        user_id=application.user_id,
        message=f"Your pass application (ID {application.id}) was rejected. Reason: {reason}"
    )
    db.session.add(notify)
    db.session.commit()

    return jsonify({"success": True, "application": application.to_dict()}), 200


@admin_bp.route("/routes", methods=["POST"])
@jwt_required()
def add_route():
    denied = _require_admin()
    if denied:
        return denied

    data = request.get_json(force=True, silent=True) or {}
    required = ["route_number", "source", "destination", "fare"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"success": False, "message": f"Missing fields: {missing}"}), 400

    if BusRoute.query.filter_by(route_number=data["route_number"]).first():
        return jsonify({"success": False, "message": "Route number already exists."}), 409

    route = BusRoute(
        route_number=data["route_number"],
        source=data["source"],
        destination=data["destination"],
        fare=float(data["fare"]),
    )
    db.session.add(route)
    db.session.commit()

    return jsonify({"success": True, "route": route.to_dict()}), 201


@admin_bp.route("/routes", methods=["GET"])
def list_routes():
    routes = BusRoute.query.all()
    return jsonify({"success": True, "routes": [r.to_dict() for r in routes]}), 200