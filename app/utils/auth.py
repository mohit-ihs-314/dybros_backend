from functools import wraps

from bson import ObjectId
from flask import jsonify
from flask_jwt_extended import (
    get_jwt,
    get_jwt_identity,
    verify_jwt_in_request,
)

from app.extensions import get_db


def role_required(required_role):
    """Protect routes using JWT role and current database account status."""

    def decorator(view_function):
        @wraps(view_function)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()

                claims = get_jwt()
                identity = get_jwt_identity()

                if claims.get("role") != required_role:
                    return jsonify({
                        "success": False,
                        "message": "You do not have permission to access this resource."
                    }), 403

                if not ObjectId.is_valid(identity):
                    return jsonify({
                        "success": False,
                        "message": "Invalid authentication identity."
                    }), 401

                db = get_db()

                collection = (
                    db.admins if required_role == "admin"
                    else db.dealers
                )

                account = collection.find_one({
                    "_id": ObjectId(identity)
                })

                if not account or not account.get("is_active", False):
                    return jsonify({
                        "success": False,
                        "message": "Account is inactive or unavailable."
                    }), 403

                if required_role == "dealer" and account.get("status") != "approved":
                    return jsonify({
                        "success": False,
                        "message": "Dealer account is not approved."
                    }), 403

                return view_function(*args, **kwargs)

            except Exception as error:
                from flask_jwt_extended.exceptions import JWTExtendedException

                if isinstance(error, JWTExtendedException):
                    return jsonify({
                        "success": False,
                        "message": "Invalid or missing authentication token."
                    }), 401

                raise

        return wrapper

    return decorator


def admin_required(view_function):
    return role_required("admin")(view_function)


def dealer_required(view_function):
    return role_required("dealer")(view_function)

def admin_or_dealer_required(view_function):
    @wraps(view_function)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()

            claims = get_jwt()
            identity = get_jwt_identity()
            role = claims.get("role")

            if role not in {"admin", "dealer"}:
                return jsonify({
                    "success": False,
                    "message": "You do not have permission to access this resource."
                }), 403

            if not ObjectId.is_valid(identity):
                return jsonify({
                    "success": False,
                    "message": "Invalid authentication identity."
                }), 401

            db = get_db()
            collection = db.admins if role == "admin" else db.dealers

            account = collection.find_one({
                "_id": ObjectId(identity)
            })

            if not account or not account.get("is_active", False):
                return jsonify({
                    "success": False,
                    "message": "Account is inactive or unavailable."
                }), 403

            if role == "dealer" and account.get("status") != "approved":
                return jsonify({
                    "success": False,
                    "message": "Dealer account is not approved."
                }), 403

            return view_function(*args, **kwargs)

        except Exception as error:
            from flask_jwt_extended.exceptions import JWTExtendedException

            if isinstance(error, JWTExtendedException):
                return jsonify({
                    "success": False,
                    "message": "Invalid or missing authentication token."
                }), 401

            raise

    return wrapper    