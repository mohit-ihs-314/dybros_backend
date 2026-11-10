
from flask import Blueprint, jsonify, request

from app.models import Dealer
from app.extensions import get_db
from app.utils.auth import admin_required
from bson import ObjectId


dealers_bp = Blueprint("dealers", __name__, url_prefix="/api/dealers")


@dealers_bp.route("", methods=["GET"])
@admin_required
def list_dealers():
    dealers = list(
        get_db().dealers.find(
            {},
            {"password_hash": 0}
        ).sort("created_at", -1)
    )

    for dealer in dealers:
        dealer["id"] = str(dealer.pop("_id"))

    return jsonify({
        "success": True,
        "total": len(dealers),
        "dealers": dealers
    }), 200


@dealers_bp.route("", methods=["POST"])
@admin_required
def create_dealer():
    data = request.get_json(silent=True) or {}

    required_fields = [
        "dealer_id",
        "business_name",
        "contact_name",
        "phone",
        "password"
    ]

    missing = [
        field for field in required_fields
        if not data.get(field)
    ]

    if missing:
        return jsonify({
            "success": False,
            "message": "Missing required fields.",
            "missing_fields": missing
        }), 400

    try:
        dealer_id = Dealer.create(
            dealer_id=data["dealer_id"],
            business_name=data["business_name"],
            contact_name=data["contact_name"],
            phone=data["phone"],
            password=data["password"],
            email=data.get("email"),
            gst_number=data.get("gst_number"),
            address=data.get("address"),
        )

        return jsonify({
            "success": True,
            "message": "Dealer account created successfully.",
            "dealer_id": dealer_id
        }), 201

    except ValueError as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 400


@dealers_bp.route("/<dealer_id>/status", methods=["PATCH"])
@admin_required
def update_dealer_status(dealer_id):
    if not ObjectId.is_valid(dealer_id):
        return jsonify({
            "success": False,
            "message": "Invalid dealer ID."
        }), 400

    data = request.get_json(silent=True) or {}
    status = data.get("status")

    try:
        updated = Dealer.update_status(dealer_id, status)

        if not updated:
            return jsonify({
                "success": False,
                "message": "Dealer not found or status unchanged."
            }), 404

        return jsonify({
            "success": True,
            "message": "Dealer status updated successfully."
        }), 200

    except ValueError as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 400
