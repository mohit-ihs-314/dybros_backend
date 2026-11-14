
from bson import ObjectId
from flask import Blueprint, jsonify, send_file
from app.utils.invoice_pdf import generate_invoice_pdf
from flask_jwt_extended import get_jwt, get_jwt_identity

from app.extensions import get_db
from app.utils.auth import admin_or_dealer_required, admin_required

invoices_bp = Blueprint(
    "invoices",
    __name__,
    url_prefix="/api/invoices"
)


def serialize_invoice(invoice):
    return {
        "id": str(invoice["_id"]),
        "invoice_number": invoice["invoice_number"],
        "order_id": str(invoice["order_id"]),
        "order_number": invoice.get("order_number"),
        "dealer_id": invoice.get("dealer_id"),
        "business_name": invoice.get("business_name"),
        "contact_name": invoice.get("contact_name"),
        "phone": invoice.get("phone"),
        "email": invoice.get("email"),
        "gst_number": invoice.get("gst_number"),
        "address": invoice.get("address"),
        "items": invoice.get("items", []),
        "subtotal": invoice.get("subtotal", 0),
        "gst_rate": invoice.get("gst_rate", 18),
        "gst": invoice.get("gst", 0),
        "total": invoice.get("total", 0),
        "payment_status": invoice.get("payment_status", "Pending"),
        "status": invoice.get("status", "Generated"),
        "invoice_date": invoice["invoice_date"].isoformat(),
        "created_at": invoice["created_at"].isoformat(),
    }


# ADMIN: Get all invoices
@invoices_bp.route("", methods=["GET"])
@admin_required
def get_all_invoices():
    invoices = list(
        get_db().invoices.find().sort("created_at", -1)
    )

    return jsonify({
        "success": True,
        "total": len(invoices),
        "invoices": [serialize_invoice(item) for item in invoices],
    }), 200


# DEALER: Get only the logged-in dealer's invoices
@invoices_bp.route("/my-invoices", methods=["GET"])
@admin_or_dealer_required
def get_my_invoices():
    claims = get_jwt()

    if claims.get("role") != "dealer":
        return jsonify({
            "success": False,
            "message": "This endpoint is for dealer accounts."
        }), 403

    dealer_id = get_jwt_identity()

    invoices = list(
        get_db().invoices.find({
            "dealer_id": dealer_id
        }).sort("created_at", -1)
    )

    return jsonify({
        "success": True,
        "total": len(invoices),
        "invoices": [serialize_invoice(item) for item in invoices],
    }), 200


# ADMIN / OWNING DEALER: Get invoice details
@invoices_bp.route("/<invoice_id>", methods=["GET"])
@admin_or_dealer_required
def get_invoice(invoice_id):
    if not ObjectId.is_valid(invoice_id):
        return jsonify({
            "success": False,
            "message": "Invalid invoice ID."
        }), 400

    invoice = get_db().invoices.find_one({
        "_id": ObjectId(invoice_id)
    })

    if not invoice:
        return jsonify({
            "success": False,
            "message": "Invoice not found."
        }), 404

    claims = get_jwt()

    if claims.get("role") == "dealer":
        if invoice.get("dealer_id") != get_jwt_identity():
            return jsonify({
                "success": False,
                "message": "You cannot access another dealer's invoice."
            }), 403

    return jsonify({
        "success": True,
        "invoice": serialize_invoice(invoice),
    }), 200


# ADMIN / OWNING DEALER: Download invoice PDF
@invoices_bp.route("/<invoice_id>/pdf", methods=["GET"])
@admin_or_dealer_required
def download_invoice_pdf(invoice_id):

    if not ObjectId.is_valid(invoice_id):
        return jsonify({
            "success": False,
            "message": "Invalid invoice ID."
        }), 400

    invoice = get_db().invoices.find_one({
        "_id": ObjectId(invoice_id)
    })

    if not invoice:
        return jsonify({
            "success": False,
            "message": "Invoice not found."
        }), 404

    claims = get_jwt()

    # Dealers can download only their own invoices
    if claims.get("role") == "dealer":
        if invoice.get("dealer_id") != get_jwt_identity():
            return jsonify({
                "success": False,
                "message": "You cannot access another dealer's invoice."
            }), 403

    pdf_buffer = generate_invoice_pdf(invoice)

    filename = f"{invoice['invoice_number']}.pdf"

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )
