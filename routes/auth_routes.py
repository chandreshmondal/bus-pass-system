import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token

from models import db, User

auth_bp = Blueprint("auth_bp", __name__)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_REGEX = re.compile(r"^\d{10}$")


def _validate_registration(data):
    """Central place for input validation - keeps bad data out of the DB."""
    errors = []

    if not data.get("name") or len(data["name"].strip()) < 2:
        errors.append("Name must be at least 2 characters.")

    if not data.get("email") or not EMAIL_REGEX.match(data["email"]):
        errors.append("A valid email is required.")

    if not data.get("phone") or not PHONE_REGEX.match(data["phone"]):
        errors.append("Phone number must be exactly 10 digits.")

    if not data.get("password") or len(data["password"]) < 6:
        errors.append("Password must be at least 6 characters.")

    return errors


@auth_bp.route("/register", methods=["POST"])
def register():
    from app import bcrypt  # imported here to avoid circular imports

    data = request.get_json(force=True, silent=True) or {}

    errors = _validate_registration(data)
    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    # Prevent duplicate accounts
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"success": False, "message": "Email already registered."}), 409
    if User.query.filter_by(phone=data["phone"]).first():
        return jsonify({"success": False, "message": "Phone already registered."}), 409

    hashed_pw = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    user = User(
        name=data["name"].strip(),
        email=data["email"].lower().strip(),
        phone=data["phone"].strip(),
        password_hash=hashed_pw,
        role="user",
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({"success": True, "message": "Registered successfully.", "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    from app import bcrypt

    data = request.get_json(force=True, silent=True) or {}
    email = data.get("email", "").lower().strip()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"success": False, "message": "Invalid email or password."}), 401

    # Token carries user id + role, so later routes know who's calling
    token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role},
    )

    return jsonify({"success": True, "access_token": token, "user": user.to_dict()}), 200