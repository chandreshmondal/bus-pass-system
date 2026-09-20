from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db, PassApplication, BusRoute, Notification

pass_bp = Blueprint("pass_bp", __name__)

VALID_PASS_TYPES = {"monthly", "quarterly", "yearly"}

# How many times the route's base fare a pass costs, per duration.
# Based on real BEST pricing patterns (quarterly = 3x monthly, roughly linear),
# with yearly getting a modest ~1-month discount vs strict 12x.
PASS_TYPE_MULTIPLIERS = {
    "monthly": 1,
    "quarterly": 3,
    "yearly": 11,
}


@pass_bp.route("/pricing/<int:route_id>", methods=["GET"])
def get_pricing(route_id):
    """Public endpoint - lets the frontend show a live price preview per pass type."""
    route = BusRoute.query.get(route_id)
    if not route:
        return jsonify({"success": False, "message": "Route does not exist."}), 404

    pricing = {
        pass_type: round(route.fare * multiplier, 2)
        for pass_type, multiplier in PASS_TYPE_MULTIPLIERS.items()
    }
    return jsonify({"success": True, "route_fare": route.fare, "pricing": pricing}), 200


@pass_bp.route("/apply", methods=["POST"])
@jwt_required()
def apply_for_pass():
    user_id = int(get_jwt_identity())
    data = request.get_json(force=True, silent=True) or {}

    route_id = data.get("route_id")
    pass_type = data.get("pass_type")

    if not route_id:
        return jsonify({"success": False, "message": "route_id is required."}), 400

    if pass_type not in VALID_PASS_TYPES:
        return jsonify({"success": False, "message": f"pass_type must be one of {list(VALID_PASS_TYPES)}."}), 400

    route = BusRoute.query.get(route_id)
    if not route:
        return jsonify({"success": False, "message": "Route does not exist."}), 404

    existing = PassApplication.query.filter_by(
        user_id=user_id, route_id=route_id
    ).filter(PassApplication.status.in_(["pending", "approved"])).first()

    if existing:
        return jsonify({
            "success": False,
            "message": f"You already have a {existing.status} application for this route."
        }), 409

    application = PassApplication(
        user_id=user_id,
        route_id=route_id,
        pass_type=pass_type,
        amount=round(route.fare * PASS_TYPE_MULTIPLIERS[pass_type], 2),
        status="pending",
    )
    db.session.add(application)
    db.session.commit()

    notify = Notification(
        user_id=user_id,
        message=f"Your application for route {route.route_number} ({route.source} → {route.destination}) has been submitted and is pending approval."
    )
    db.session.add(notify)
    db.session.commit()

    return jsonify({"success": True, "application": application.to_dict()}), 201


@pass_bp.route("/my-applications", methods=["GET"])
@jwt_required()
def my_applications():
    user_id = int(get_jwt_identity())
    apps = PassApplication.query.filter_by(user_id=user_id).order_by(PassApplication.applied_on.desc()).all()
    return jsonify({"success": True, "applications": [a.to_dict() for a in apps]}), 200


@pass_bp.route("/status/<int:application_id>", methods=["GET"])
@jwt_required()
def check_status(application_id):
    user_id = int(get_jwt_identity())
    application = PassApplication.query.get(application_id)

    if not application or application.user_id != user_id:
        return jsonify({"success": False, "message": "Application not found."}), 404

    return jsonify({"success": True, "status": application.status, "application": application.to_dict()}), 200


@pass_bp.route("/renew/<int:application_id>", methods=["POST"])
@jwt_required()
def renew_pass(application_id):
    user_id = int(get_jwt_identity())
    application = PassApplication.query.get(application_id)

    if not application or application.user_id != user_id:
        return jsonify({"success": False, "message": "Application not found."}), 404

    if application.status != "approved":
        return jsonify({"success": False, "message": "Only approved passes can be renewed."}), 400

    application.status = "expired"
    new_application = PassApplication(
        user_id=user_id,
        route_id=application.route_id,
        pass_type=application.pass_type,
        amount=application.amount,
        status="pending",
    )
    db.session.add(new_application)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Renewal submitted for approval.",
        "new_application": new_application.to_dict()
    }), 201


@pass_bp.route("/notifications", methods=["GET"])
@jwt_required()
def get_notifications():
    user_id = int(get_jwt_identity())
    notes = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
    unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    return jsonify({
        "success": True,
        "notifications": [n.to_dict() for n in notes],
        "unread_count": unread_count,
    }), 200


@pass_bp.route("/notifications/read", methods=["POST"])
@jwt_required()
def mark_notifications_read():
    user_id = int(get_jwt_identity())
    Notification.query.filter_by(user_id=user_id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"success": True, "message": "All notifications marked as read."}), 200


@pass_bp.route("/verify/<int:application_id>", methods=["GET"])
def verify_pass(application_id):
    """Public endpoint for QR scanning - only exposes minimal, non-sensitive info."""
    application = PassApplication.query.get(application_id)

    if not application:
        return jsonify({"success": False, "valid": False, "message": "Pass not found."}), 404

    is_valid = application.status == "approved"

    return jsonify({
        "success": True,
        "valid": is_valid,
        "status": application.status,
        "pass_type": application.pass_type,
        "route": application.route.route_number if application.route else None,
    }), 200