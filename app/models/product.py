
from datetime import datetime, timezone

from bson import ObjectId

from app.extensions import get_db


class Product:
    COLLECTION = "products"

    @staticmethod
    def create(
        name: str,
        sku: str,
        spec: str,
        price: float,
        moq: int,
        stock: int,
        category: str,
        image: str = None,
        tone: str = None,
        created_by: str = None,
        brand: str = None,
        model: str = None,
        variety: str = None,
        images: list = None,
        description: str = None,
    ) -> str:

        name = name.strip()
        sku = sku.strip().upper()
        category = category.strip()

        if not all([name, sku, category]):
            raise ValueError("Product name, SKU and category are required.")

        if price < 0:
            raise ValueError("Price cannot be negative.")

        if moq < 1:
            raise ValueError("Minimum order quantity must be at least 1.")

        if stock < 0:
            raise ValueError("Stock cannot be negative.")

        db = get_db()

        if db.products.find_one({"sku": sku}):
            raise ValueError("A product with this SKU already exists.")

        now = datetime.now(timezone.utc)

        clean_images = [
            url.strip()
            for url in (images or [])
            if isinstance(url, str) and url.strip()
        ]

        if image and image.strip() and image.strip() not in clean_images:
            clean_images.insert(0, image.strip())

        product = {
            "name": name,
            "sku": sku,
            "spec": spec.strip() if spec else "",
            "price": round(float(price), 2),
            "moq": int(moq),
            "stock": int(stock),
            "category": category,
            "brand": brand.strip() if brand else None,
            "model": model.strip() if model else None,
            "variety": variety.strip() if variety else None,
            "description": description.strip() if description else "",
            "image": clean_images[0] if clean_images else (
                image.strip() if image else None
            ),
            "images": clean_images,
            "tone": tone.strip() if tone else None,
            "is_active": True,
            "created_by": created_by,
            "created_at": now,
            "updated_at": now,
        }

        result = db.products.insert_one(product)
        return str(result.inserted_id)

    @staticmethod
    def get_by_id(product_id: str):
        if not ObjectId.is_valid(product_id):
            return None

        return get_db().products.find_one({
            "_id": ObjectId(product_id)
        })

    @staticmethod
    def get_by_sku(sku: str):
        if not sku:
            return None

        return get_db().products.find_one({
            "sku": sku.strip().upper()
        })

    @staticmethod
    def get_all(active_only=True):
        query = {"is_active": True} if active_only else {}

        return list(
            get_db().products.find(query).sort("created_at", -1)
        )

    @staticmethod
    def update(product_id: str, updates: dict):
        if not ObjectId.is_valid(product_id):
            raise ValueError("Invalid product ID.")

        allowed_fields = {
            "name", "spec", "price", "moq",
            "stock", "category", "image", "tone",
            "brand", "model", "variety",
            "images", "description",
        }

        clean_updates = {
            key: value
            for key, value in updates.items()
            if key in allowed_fields
        }

        if not clean_updates:
            raise ValueError("No valid product fields provided.")

        for field in [
            "name", "category", "brand",
            "model", "variety", "description",
            "spec", "image", "tone",
        ]:
            if field in clean_updates:
                value = clean_updates[field]

                if value is None and field in {
                    "brand", "model", "variety", "image", "tone"
                }:
                    continue

                if not isinstance(value, str):
                    raise ValueError(f"{field} must be a string.")

                clean_updates[field] = value.strip()

        if "price" in clean_updates:
            price = float(clean_updates["price"])

            if price < 0:
                raise ValueError("Price cannot be negative.")

            clean_updates["price"] = round(price, 2)

        if "moq" in clean_updates:
            moq = int(clean_updates["moq"])

            if moq < 1:
                raise ValueError("MOQ must be at least 1.")

            clean_updates["moq"] = moq

        if "stock" in clean_updates:
            stock = int(clean_updates["stock"])

            if stock < 0:
                raise ValueError("Stock cannot be negative.")

            clean_updates["stock"] = stock

        if "images" in clean_updates:
            images = clean_updates["images"]

            if not isinstance(images, list):
                raise ValueError("Images must be a list.")

            clean_updates["images"] = [
                url.strip()
                for url in images
                if isinstance(url, str) and url.strip()
            ]

            if clean_updates["images"]:
                clean_updates["image"] = clean_updates["images"][0]

        clean_updates["updated_at"] = datetime.now(timezone.utc)

        result = get_db().products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": clean_updates}
        )

        return result.modified_count > 0

    @staticmethod
    def deactivate(product_id: str):
        if not ObjectId.is_valid(product_id):
            raise ValueError("Invalid product ID.")

        result = get_db().products.update_one(
            {"_id": ObjectId(product_id)},
            {
                "$set": {
                    "is_active": False,
                    "updated_at": datetime.now(timezone.utc),
                }
            }
        )

        return result.modified_count > 0
