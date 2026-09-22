from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="user")  # 'user' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship("PassApplication", backref="applicant", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
        }


class BusRoute(db.Model):
    __tablename__ = "bus_routes"

    id = db.Column(db.Integer, primary_key=True)
    route_number = db.Column(db.String(20), unique=True, nullable=False)
    source = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    fare = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "route_number": self.route_number,
            "source": self.source,
            "destination": self.destination,
            "fare": self.fare,
        }


class PassApplication(db.Model):
    __tablename__ = "pass_applications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey("bus_routes.id"), nullable=False)

    pass_type = db.Column(db.String(20), nullable=False)  # 'monthly', 'quarterly', 'yearly'
    trip_type = db.Column(db.String(20), nullable=False, default="one_way")  # 'one_way' or 'round_trip'
    amount = db.Column(db.Float, nullable=True)  # calculated price, set at application time

    # Applicant details collected per-application (demo only - see note on Aadhar below)
    applicant_age = db.Column(db.Integer, nullable=True)
    applicant_mobile = db.Column(db.String(15), nullable=True)
    # NOTE: stored plain for academic demo purposes only. A real production system
    # must not store raw Aadhar numbers without proper UIDAI authorization under
    # the Aadhaar Act - this would normally be masked or tokenized.
    aadhar_number = db.Column(db.String(20), nullable=True)

    status = db.Column(db.String(20), default="pending")  # pending/approved/rejected
    rejection_reason = db.Column(db.String(255), nullable=True)
    applied_on = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_on = db.Column(db.DateTime, nullable=True)

    route = db.relationship("BusRoute")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.applicant.name if self.applicant else None,
            "user_email": self.applicant.email if self.applicant else None,
            "route": self.route.to_dict() if self.route else None,
            "pass_type": self.pass_type,
            "trip_type": self.trip_type,
            "amount": self.amount,
            "applicant_age": self.applicant_age,
            "applicant_mobile": self.applicant_mobile,
            "aadhar_number": self.aadhar_number,
            "status": self.status,
            "rejection_reason": self.rejection_reason,
            "applied_on": self.applied_on.isoformat(),
            "reviewed_on": self.reviewed_on.isoformat() if self.reviewed_on else None,
        }


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "message": self.message,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
        }