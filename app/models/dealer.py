from datetime import datetime, timezone

from bson import ObjectId
from app.extensions import get_db
from app.models.accounts import hash_password, verify_password


class Dealer:
    COLLECTION = "dealers"

    @staticmethod
    def create(
        dealer_id: str,
        business_name: str,
        contact_name: str,
        phone: str,
        password: str,
        email: str = None,
        gst_number: str = None,
        address: str = None,
        created_by: str = None,
    ) -> str:

        dealer_id = dealer_id.strip().upper()
        business_name = business_name.strip()
        contact_name = contact_name.strip()
        phone = phone.strip()

        if not all([dealer_id, business_name, contact_name, phone, password]):
            raise ValueError("All required dealer fields must be provided.")

        if len(password) < 12:
            raise ValueError("Dealer password must be at least 12 characters.")

        db = get_db()

        if db.dealers.find_one({"dealer_id": dealer_id}):
            raise ValueError("Dealer ID already exists.")

        if email:
            email = email.strip().lower()
            if db.dealers.find_one({"email": email}):
                raise ValueError("Dealer email already exists.")

        now = datetime.now(timezone.utc)

        dealer = {
            "dealer_id": dealer_id,
            "business_name": business_name,
            "contact_name": contact_name,
            "phone": phone,
            "email": email,
            "gst_number": gst_number.strip() if gst_number else None,
            "address": address.strip() if address else None,
            "password_hash": hash_password(password),
            "status": "approved",
            "is_active": True,
            "must_change_password": True,
            "created_by": created_by,
            "created_at": now,
            "updated_at": now,
        }

        result = db.dealers.insert_one(dealer)
        return str(result.inserted_id)

    @staticmethod
    def find_by_dealer_id(dealer_id: str):
        if not dealer_id:
            return None

        return get_db().dealers.find_one({
            "dealer_id": dealer_id.strip().upper()
        })

    @staticmethod
    def authenticate(identifier: str, password: str):
        if not identifier or not password:
            return None

        identifier = identifier.strip()

        dealer = get_db().dealers.find_one({
            "$or": [
                {"dealer_id": identifier.upper()},
                {"email": identifier.lower()},
            ]
        })

        if not dealer:
            return None

        if dealer.get("status") != "approved":
            return None

        if not dealer.get("is_active", False):
            return None

        if not verify_password(dealer.get("password_hash"), password):
            return None

        return dealer

    @staticmethod
    def get_by_id(dealer_id: str):
        try:
            return get_db().dealers.find_one({
                "_id": ObjectId(dealer_id)
            })
        except Exception:
            return None

    @staticmethod
    def update_status(dealer_id: str, status: str):
        allowed_statuses = {"approved", "suspended"}

        if status not in allowed_statuses:
            raise ValueError("Invalid dealer status.")

        result = get_db().dealers.update_one(
            {"_id": ObjectId(dealer_id)},
            {
                "$set": {
                    "status": status,
                    "is_active": status == "approved",
                    "updated_at": datetime.now(timezone.utc),
                }
            }
        )

        return result.modified_count > 0

    
    @staticmethod
    def reset_password(dealer_id: str, new_password: str):
        if not new_password or len(new_password) < 12:
            raise ValueError(
                "Password must be at least 12 characters."
            )

        result = get_db().dealers.update_one(
            {"_id": ObjectId(dealer_id)},
            {
                "$set": {
                    "password_hash": hash_password(new_password),
                    "must_change_password": True,
                    "updated_at": datetime.now(timezone.utc),
                }
            }
        )

        return result.matched_count > 0

    
    @staticmethod
    def change_password(dealer_id: str, current_password: str, new_password: str):
        if not current_password or not new_password:
            raise ValueError("Current and new passwords are required.")

        if len(new_password) < 12:
            raise ValueError("New password must be at least 12 characters.")

        dealer = Dealer.get_by_id(dealer_id)

        if not dealer:
            return False

        if not verify_password(dealer.get("password_hash"), current_password):
            raise ValueError("Current password is incorrect.")

        result = get_db().dealers.update_one(
            {"_id": ObjectId(dealer_id)},
            {
                "$set": {
                    "password_hash": hash_password(new_password),
                    "must_change_password": False,
                    "updated_at": datetime.now(timezone.utc),
                }
            }
        )

        return result.matched_count > 0
    
    