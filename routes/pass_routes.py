from datetime import datetime
import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db, PassApplication, BusRoute, Notification

pass_bp = Blueprint("pass_bp", __name__)

MOBILE_REGEX = re.compile(r"^\d{10}$")
AADHAR_REGEX = re.compile(r"^\d{12}$")

VALID_PASS_TYPES = {"daily", "monthly", "quarterly", "yearly"}

# Each pass type's price = route fare x trip type multiplier x this many "days",
# with a discount baked in for longer commitments (no discount on daily).
# Based on real BEST data (~15% monthly discount vs per-trip cost), scaled up
# for quarterly/yearly to reward longer commitments.
PASS_TYPE_MULTIPLIERS = {
    "daily": 1 * 1,           # no discount
    "monthly": 28 * 0.85,     # 15% off
    "quarterly": 84 * 0.80,   # 20% off
    "yearly": 308 * 0.70,     # 30% off
}

VALID_TRIP_TYPES = {"one_way", "round_trip"}
TRIP_TYPE_MULTIPLIERS = {
    "one_way": 1,
    "round_trip": 2,
}


@pass_bp.route("/pricing/<int:route_id>", methods=["GET"])
def get_pricing(route_id):
    """Public endpoint - lets the frontend show a live price preview per pass type and trip type."""
    route = BusRoute.query.get(route_id)
    if not route:
        return jsonify({"success": False, "message": "Route does not exist."}), 404

    pricing = {}
    for pass_type, pass_mult in PASS_TYPE_MULTIPLIERS.items():
        pricing[pass_type] = {
            trip_type: round(route.fare * pass_mult * trip_mult, 2)
            for trip_type, trip_mult in TRIP_TYPE_MULTIPLIERS.items()
        }

    return jsonify({"success": True, "route_fare": route.fare, "pricing": pricing}), 200


@pass_bp.route("/apply", methods=["POST"])
@jwt_required()
def apply_for_pass():
    user_id = int(get_jwt_identity())
    data = request.get_json(force=True, silent=True) or {}

    route_id = data.get("route_id")
    pass_type = data.get("pass_type")
    trip_type = data.get("trip_type", "one_way")  # defaults to one-way if not sent
    applicant_age = data.get("applicant_age")
    applicant_mobile = data.get("applicant_mobile")
    aadhar_number = data.get("aadhar_number")

    if not route_id:
        return jsonify({"success": False, "message": "route_id is required."}), 400

    if pass_type not in VALID_PASS_TYPES:
        return jsonify({"success": False, "message": f"pass_type must be one of {list(VALID_PASS_TYPES)}."}), 400

    if trip_type not in VALID_TRIP_TYPES:
        return jsonify({"success": False, "message": f"trip_type must be one of {list(VALID_TRIP_TYPES)}."}), 400

    if applicant_age is not None:
        try:
            applicant_age = int(applicant_age)
            if not (5 <= applicant_age <= 100):
                return jsonify({"success": False, "message": "applicant_age must be between 5 and 100."}), 400
        except (TypeError, ValueError):
            return jsonify({"success": False, "message": "applicant_age must be a number."}), 400

    if applicant_mobile and not MOBILE_REGEX.match(applicant_mobile):
        return jsonify({"success": False, "message": "applicant_mobile must be exactly 10 digits."}), 400

    if aadhar_number and not AADHAR_REGEX.match(aadhar_number.replace(" ", "").replace("-", "")):
        return jsonify({"success": False, "message": "aadhar_number must be exactly 12 digits."}), 400

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
        trip_type=trip_type,
        amount=round(route.fare * PASS_TYPE_MULTIPLIERS[pass_type] * TRIP_TYPE_MULTIPLIERS[trip_type], 2),
        applicant_age=applicant_age,
        applicant_mobile=applicant_mobile,
        aadhar_number=aadhar_number,
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
        trip_type=application.trip_type,
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
        "trip_type": application.trip_type,
        "route": application.route.route_number if application.route else None,
    }), 200