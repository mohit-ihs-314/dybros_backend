
from datetime import datetime, timezone
from secrets import token_hex
from pymongo.errors import DuplicateKeyError
from bson import ObjectId

from app.extensions import get_db


class Invoice:

    @staticmethod
    def create(order):
        """
        Generate an invoice from an existing MongoDB order.
        Stores a snapshot of dealer and product information.
        """

        if not order:
            raise ValueError("Order information is required.")

        db = get_db()

        order_id = order.get("_id")

        if not isinstance(order_id, ObjectId):
            raise ValueError("Invalid order ID.")

        # Prevent duplicate invoices for the same order.
        existing = db.invoices.find_one({
            "order_id": order_id
        })

        if existing:
            return existing

        now = datetime.now(timezone.utc)
        invoice_number = (
            f"INV-{now.year}-{token_hex(4).upper()}"
        )

        invoice = {
            "invoice_number": invoice_number,
            "order_id": order_id,
            "order_number": order.get("order_number"),

            # Dealer snapshot
            "dealer_id": order.get("dealer_id"),
            "business_name": order.get("business_name"),
            "contact_name": order.get("contact_name"),
            "phone": order.get("phone"),
            "email": order.get("email"),
            "gst_number": order.get("gst_number"),
            "address": order.get("address"),

            # Product snapshot
            "items": order.get("items", []),

            # Financial details
            "subtotal": order.get("subtotal", 0),
            "gst_rate": order.get("gst_rate", 18),
            "gst": order.get("gst", 0),
            "total": order.get("total", 0),

            "payment_status": order.get("payment_status", "Pending"),
            "status": "Generated",

            "invoice_date": now,
            "created_at": now,
            "updated_at": now,
        }

        try:
            db.invoices.insert_one(invoice)
        except DuplicateKeyError:
            return db.invoices.find_one({
                "order_id": order_id
            })

        return db.invoices.find_one({
            "order_id": order_id
        })
