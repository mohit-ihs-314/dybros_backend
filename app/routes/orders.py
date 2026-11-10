from datetime import datetime, timezone
from bson import ObjectId
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from app.extensions import get_db
from app.models import Order
from app.utils.auth import (
    admin_or_dealer_required,
    admin_required,
    dealer_required,
)

orders_bp = Blueprint("orders", __name__, url_prefix="/api/orders")


def serialize_order(order):
    return {
        "id": str(order["_id"]),
        "order_number": order["order_number"],
        "dealer_id": order["dealer_id"],
        "dealer_code": order.get("dealer_code"),
        "business_name": order.get("business_name"),
        "contact_name": order.get("contact_name"),
        "phone": order.get("phone"),
        "email": order.get("email"),
        "gst_number": order.get("gst_number"),
        "address": order.get("address"),
        "items": [
            {
                "product_id": item["product_id"],
                "name": item["name"],
                "sku": item["sku"],
                "price": item["price"],
                "quantity": item["quantity"],
                "line_total": item["line_total"],
            }
            for item in order.get("items", [])
        ],
        "subtotal": order["subtotal"],
        "gst_rate": order["gst_rate"],
        "gst": order["gst"],
        "total": order["total"],
        "notes": order.get("notes", ""),
        "status": order["status"],
        "payment_status": order["payment_status"],
        "created_at": order["created_at"].astimezone(timezone.utc).isoformat(),
        "updated_at": order["updated_at"].astimezone(timezone.utc).isoformat(),
    }


@orders_bp.route("", methods=["POST"])
@dealer_required
def create_order():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "A valid JSON request body is required."
        }), 400

    items = data.get("items")
    notes = data.get("notes", "")

    if not isinstance(notes, str):
        return jsonify({
            "success": False,
            "message": "Order notes must be text."
        }), 400

    try:
        order = Order.create(
            dealer_id=get_jwt_identity(),
            items=items,
            notes=notes,
        )

        return jsonify({
            "success": True,
            "message": "Order placed successfully.",
            "order": serialize_order(order),
        }), 201

    except (ValueError, TypeError) as error:
        return jsonify({
            "success": False,
            "message": str(error),
        }), 400


@orders_bp.route("", methods=["GET"])
@admin_required
def get_all_orders():
    orders = list(
        get_db().orders.find().sort("created_at", -1)
    )

    return jsonify({
        "success": True,
        "total": len(orders),
        "orders": [serialize_order(order) for order in orders],
    }), 200


@orders_bp.route("/my-orders", methods=["GET"])
@dealer_required
def get_my_orders():
    dealer_id = get_jwt_identity()

    orders = list(
        get_db().orders.find({
            "dealer_id": dealer_id
        }).sort("created_at", -1)
    )

    return jsonify({
        "success": True,
        "total": len(orders),
        "orders": [serialize_order(order) for order in orders],
    }), 200


@orders_bp.route("/<order_id>", methods=["GET"])
@admin_or_dealer_required
def get_order(order_id):
    if not ObjectId.is_valid(order_id):
        return jsonify({
            "success": False,
            "message": "Invalid order ID."
        }), 400

    order = get_db().orders.find_one({
        "_id": ObjectId(order_id)
    })

    if not order:
        return jsonify({
            "success": False,
            "message": "Order not found."
        }), 404

    from flask_jwt_extended import get_jwt

    if get_jwt().get("role") == "dealer":
        if order.get("dealer_id") != get_jwt_identity():
            return jsonify({
                "success": False,
                "message": "You cannot access another dealer's order."
            }), 403

    return jsonify({
        "success": True,
        "order": serialize_order(order),
    }), 200


@orders_bp.route("/<order_id>/status", methods=["PATCH"])
@admin_required
def update_order_status(order_id):
    if not ObjectId.is_valid(order_id):
        return jsonify({
            "success": False,
            "message": "Invalid order ID."
        }), 400

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "A valid JSON request body is required."
        }), 400

    allowed_statuses = {
        "Awaiting Confirmation",
        "Confirmed",
        "Processing",
        "Dispatched",
        "Delivered",
        "Cancelled",
    }

    allowed_payment_statuses = {
        "Pending",
        "Part Paid",
        "Paid",
    }

    updates = {}

    if "status" in data:
        status = data["status"]

        if status not in allowed_statuses:
            return jsonify({
                "success": False,
                "message": "Invalid order status."
            }), 400

        updates["status"] = status

    if "payment_status" in data:
        payment_status = data["payment_status"]

        if payment_status not in allowed_payment_statuses:
            return jsonify({
                "success": False,
                "message": "Invalid payment status."
            }), 400

        updates["payment_status"] = payment_status

    if not updates:
        return jsonify({
            "success": False,
            "message": "Provide an order status or payment status to update."
        }), 400

    updates["updated_at"] = datetime.now(timezone.utc)

    db = get_db()

    result = db.orders.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": updates}
    )

    if result.matched_count == 0:
        return jsonify({
            "success": False,
            "message": "Order not found."
        }), 404

    updated_order = db.orders.find_one({
        "_id": ObjectId(order_id)
    })

    return jsonify({
        "success": True,
        "message": "Order updated successfully.",
        "order": serialize_order(updated_order),
    }), 200
