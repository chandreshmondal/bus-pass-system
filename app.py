from flask import Flask, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from config import Config
from models import db, User

bcrypt = Bcrypt()
jwt = JWTManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, resources={r"/api/*": {"origins": [
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://buss-pass-frontend.onrender.com",
    ]}}, supports_credentials=True)

    # Attach extensions to the app
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Register blueprints (each file in routes/ is a separate "module" of endpoints)
    from routes.auth_routes import auth_bp
    from routes.pass_routes import pass_bp
    from routes.admin_routes import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(pass_bp, url_prefix="/api/passes")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    # Create tables and a default admin account if none exists
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(role="admin").first():
            admin = User(
                name="System Admin",
                email="admin@buspass.com",
                phone="0000000000",
                password_hash=bcrypt.generate_password_hash("admin123").decode("utf-8"),
                role="admin",
            )
            db.session.add(admin)
            db.session.commit()
            print("Default admin created -> email: admin@buspass.com | password: admin123")

    # Return JSON instead of Flask's default HTML error pages -
    # keeps every response from this API consistent.
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            "success": False,
            "message": "This endpoint does not exist. Check the URL and method."
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({
            "success": False,
            "message": "This HTTP method is not allowed on this endpoint."
        }), 405

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({
            "success": False,
            "message": "Something went wrong on the server."
        }), 500

    # TEMPORARY - remove this route after running it once
    @app.route("/api/maintenance/add-amount-column")
    def add_amount_column():
        from sqlalchemy import text
        try:
            with db.engine.connect() as conn:
                conn.execute(text(
                    "ALTER TABLE pass_applications ADD COLUMN IF NOT EXISTS amount FLOAT;"
                ))
                conn.commit()
            return jsonify({"success": True, "message": "Column added successfully."}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    return app


# Create a plain module-level app object - more reliable than gunicorn's
# factory-call syntax across different gunicorn versions.
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)