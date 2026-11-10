
from flask import Blueprint, current_app, jsonify
from app.extensions import get_db


health_bp = Blueprint("health", __name__)


@health_bp.route("/api/health", methods=["GET"])
def health_check():
    """
    Check whether the DYABROS API is running.
    """

    return jsonify({
        "success": True,
        "message": "DYABROS API is running",
        "service": "Flask Backend"
    }), 200


@health_bp.route("/api/health/database", methods=["GET"])
def database_health_check():
    """
    Check MongoDB database connectivity.
    """

    try:
        database = get_db()
        database.command("ping")

        return jsonify({
            "success": True,
            "message": "MongoDB Atlas connected successfully",
            "database": current_app.config["MONGO_DB_NAME"]
        }), 200

    except Exception:
        current_app.logger.exception(
            "MongoDB health check failed"
        )

        return jsonify({
            "success": False,
            "message": "MongoDB connection failed"
        }), 503
