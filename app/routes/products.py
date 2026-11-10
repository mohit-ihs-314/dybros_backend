
from flask import Blueprint, jsonify, request

from app.models import Product
from app.utils.auth import admin_required, admin_or_dealer_required

products_bp = Blueprint(
    "products",
    __name__,
    url_prefix="/api/products"
)


def serialize_product(product, include_private=True):
    result = {
        "id": str(product["_id"]),
        "name": product.get("name", ""),
        "sku": product.get("sku", ""),
        "spec": product.get("spec", ""),
        "category": product.get("category", ""),
        "brand": product.get("brand"),
        "model": product.get("model"),
        "variety": product.get("variety"),
        "description": product.get("description", ""),
        "image": product.get("image"),
        "images": product.get("images", []),
        "tone": product.get("tone"),
        "is_active": product.get("is_active", True),
    }

    if include_private:
        result.update({
            "price": product.get("price", 0),
            "moq": product.get("moq", 1),
            "stock": product.get("stock", 0),
        })

    return result


# PUBLIC CATALOGUE — no price, MOQ or stock
@products_bp.route("/public", methods=["GET"])
def get_public_products():
    products = Product.get_all(active_only=True)

    return jsonify({
        "success": True,
        "total": len(products),
        "products": [
            serialize_product(product, include_private=False)
            for product in products
        ]
    }), 200


# DEALER / ADMIN CATALOGUE — includes pricing
@products_bp.route("", methods=["GET"])
@admin_or_dealer_required
def get_products():
    products = Product.get_all(active_only=True)

    return jsonify({
        "success": True,
        "total": len(products),
        "products": [
            serialize_product(product)
            for product in products
        ]
    }), 200


# ADMIN — all products, including inactive
@products_bp.route("/all", methods=["GET"])
@admin_required
def get_all_products():
    products = Product.get_all(active_only=False)

    return jsonify({
        "success": True,
        "total": len(products),
        "products": [
            serialize_product(product)
            for product in products
        ]
    }), 200


# ADMIN — create product
@products_bp.route("", methods=["POST"])
@admin_required
def create_product():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "A valid JSON request body is required."
        }), 400

    required_fields = [
        "name", "sku", "price", "moq",
        "stock", "category"
    ]

    missing_fields = [
        field for field in required_fields
        if field not in data or data[field] is None
    ]

    if missing_fields:
        return jsonify({
            "success": False,
            "message": "Missing required fields.",
            "fields": missing_fields
        }), 400

    try:
        product_id = Product.create(
            name=data["name"],
            sku=data["sku"],
            spec=data.get("spec", ""),
            price=float(data["price"]),
            moq=int(data["moq"]),
            stock=int(data["stock"]),
            category=data["category"],
            image=data.get("image"),
            tone=data.get("tone"),
            brand=data.get("brand"),
            model=data.get("model"),
            variety=data.get("variety"),
            images=data.get("images"),
            description=data.get("description", ""),
        )

        product = Product.get_by_id(product_id)

        return jsonify({
            "success": True,
            "message": "Product created successfully.",
            "product": serialize_product(product)
        }), 201

    except (ValueError, TypeError) as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 400


# ADMIN — update product
@products_bp.route("/<product_id>", methods=["PUT"])
@admin_required
def update_product(product_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "A valid JSON request body is required."
        }), 400

    try:
        product = Product.get_by_id(product_id)

        if not product:
            return jsonify({
                "success": False,
                "message": "Product not found."
            }), 404

        allowed_fields = {
            "name", "spec", "price", "moq",
            "stock", "category", "image", "tone",
            "brand", "model", "variety",
            "images", "description",
        }

        updates = {
            key: value
            for key, value in data.items()
            if key in allowed_fields
        }

        if not updates:
            return jsonify({
                "success": False,
                "message": "No valid product fields provided."
            }), 400

        Product.update(product_id, updates)
        updated_product = Product.get_by_id(product_id)

        return jsonify({
            "success": True,
            "message": "Product updated successfully.",
            "product": serialize_product(updated_product)
        }), 200

    except (ValueError, TypeError) as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 400
