from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)

from app.models import Admin, Dealer

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required."
        }), 400

    admin = Admin.authenticate(email, password)

    if not admin:
        return jsonify({
            "success": False,
            "message": "Invalid credentials or inactive account."
        }), 401

    token = create_access_token(
        identity=str(admin["_id"]),
        additional_claims={"role": "admin"}
    )

    return jsonify({
        "success": True,
        "message": "Admin login successful.",
        "access_token": token,
        "user": {
            "id": str(admin["_id"]),
            "name": admin["name"],
            "email": admin["email"],
            "role": "admin"
        }
    }), 200


@auth_bp.route("/dealer/login", methods=["POST"])
def dealer_login():
    data = request.get_json(silent=True) or {}

    identifier = data.get("identifier", "").strip()
    password = data.get("password", "")

    if not identifier or not password:
        return jsonify({
            "success": False,
            "message": "Dealer ID/email and password are required."
        }), 400

    dealer = Dealer.authenticate(identifier, password)

    if not dealer:
        return jsonify({
            "success": False,
            "message": "Invalid credentials or inactive account."
        }), 401

    token = create_access_token(
        identity=str(dealer["_id"]),
        additional_claims={"role": "dealer"}
    )

    return jsonify({
        "success": True,
        "message": "Dealer login successful.",
        "access_token": token,
        "must_change_password": dealer.get("must_change_password", False),
        "user": {
            "id": str(dealer["_id"]),
            "dealer_id": dealer["dealer_id"],
            "business_name": dealer["business_name"],
            "contact_name": dealer["contact_name"],
            "email": dealer.get("email"),
            "phone": dealer.get("phone", ""),
            "gst_number": dealer.get("gst_number", ""),
            "address": dealer.get("address", ""),
            "role": "dealer"
        }
    }), 200


@auth_bp.route("/dealer/change-password", methods=["POST"])
@jwt_required()
def dealer_change_password():
    claims = get_jwt()

    if claims.get("role") != "dealer":
        return jsonify({
            "success": False,
            "message": "Dealer access required."
        }), 403

    data = request.get_json(silent=True) or {}

    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    try:
        updated = Dealer.change_password(
            dealer_id=get_jwt_identity(),
            current_password=current_password,
            new_password=new_password
        )

        if not updated:
            return jsonify({
                "success": False,
                "message": "Dealer account not found."
            }), 404

        return jsonify({
            "success": True,
            "message": "Password changed successfully."
        }), 200

    except ValueError as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 400
