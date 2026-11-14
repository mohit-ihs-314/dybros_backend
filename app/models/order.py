from datetime import datetime, timezone
from bson import ObjectId
from app.extensions import get_db
import secrets


class Order:

    COLLECTION = "orders"
    GST_RATE = 0.18

    @staticmethod
    def create(dealer_id: str, items: list, notes: str = ""):

        db = get_db()

        if not ObjectId.is_valid(dealer_id):
            raise ValueError("Invalid dealer account.")

        if not isinstance(items, list) or not items:
            raise ValueError("Your cart is empty.")

        dealer = db.dealers.find_one({
            "_id": ObjectId(dealer_id)
        })

        if not dealer:
            raise ValueError("Dealer account not found.")

        order_items = []
        subtotal = 0

        for item in items:

            product_id = item.get("productId")
            quantity = item.get("quantity")

            if not ObjectId.is_valid(str(product_id)):
                raise ValueError("Invalid product ID.")

            try:
                quantity = int(quantity)
            except (TypeError, ValueError):
                raise ValueError("Invalid product quantity.")

            if quantity < 1:
                raise ValueError("Quantity must be at least 1.")

            product = db.products.find_one({
                "_id": ObjectId(str(product_id)),
                "is_active": True
            })

            if not product:
                raise ValueError("One or more products are unavailable.")

            if quantity < product["moq"]:
                raise ValueError(
                    f'{product["name"]}: Minimum order quantity is {product["moq"]}.'
                )

            if quantity > product["stock"]:
                raise ValueError(
                    f'{product["name"]}: Only {product["stock"]} units available.'
                )

            price = round(float(product["price"]), 2)
            line_total = round(price * quantity, 2)

            subtotal += line_total

            order_items.append({
                "product_id": str(product["_id"]),
                "name": product["name"],
                "sku": product["sku"],
                "price": price,
                "quantity": quantity,
                "line_total": line_total
            })

        subtotal = round(subtotal, 2)
        gst = round(subtotal * Order.GST_RATE, 2)
        total = round(subtotal + gst, 2)

        now = datetime.now(timezone.utc)

        order_number = (
            f"ORD-{now.strftime('%Y')}-"
            f"{secrets.token_hex(4).upper()}"
        )

        order = {
            "order_number": order_number,
            "dealer_id": str(dealer["_id"]),
            "dealer_code": dealer["dealer_id"],
            "business_name": dealer["business_name"],
            "contact_name": dealer["contact_name"],
            "phone": dealer["phone"],
            "email": dealer.get("email"),
            "gst_number": dealer.get("gst_number"),
            "address": dealer.get("address"),

            "items": order_items,

            "subtotal": subtotal,
            "gst_rate": Order.GST_RATE,
            "gst": gst,
            "total": total,

            "notes": notes.strip() if isinstance(notes, str) else "",

            "status": "Awaiting Confirmation",
            "payment_status": "Pending",

            # Payment tracking
            "amount_paid": 0.0,
            "outstanding_amount": total,
            "payments": [],

            "created_at": now,
            "updated_at": now
        }

        result = db.orders.insert_one(order)
        order["_id"] = result.inserted_id
        return order