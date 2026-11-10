from datetime import datetime, timezone

from bson import ObjectId
from app.extensions import get_db
from app.models.accounts import hash_password, verify_password


class Admin:
    COLLECTION = "admins"

    @staticmethod
    def create(name: str, email: str, password: str) -> str:
        name = name.strip()
        email = email.strip().lower()

        if not name or not email or not password:
            raise ValueError("Name, email and password are required.")

        if len(password) < 12:
            raise ValueError("Admin password must be at least 12 characters.")

        db = get_db()

        if db.admins.find_one({"email": email}):
            raise ValueError("An admin with this email already exists.")

        now = datetime.now(timezone.utc)

        admin = {
            "name": name,
            "email": email,
            "password_hash": hash_password(password),
            "role": "admin",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }

        result = db.admins.insert_one(admin)
        return str(result.inserted_id)

    @staticmethod
    def find_by_email(email: str):
        if not email:
            return None

        return get_db().admins.find_one({
            "email": email.strip().lower()
        })

    @staticmethod
    def authenticate(email: str, password: str):
        admin = Admin.find_by_email(email)

        if not admin or not admin.get("is_active", False):
            return None

        if not verify_password(admin.get("password_hash"), password):
            return None

        return admin

    @staticmethod
    def get_by_id(admin_id: str):
        try:
            return get_db().admins.find_one({
                "_id": ObjectId(admin_id)
            })
        except Exception:
            return None