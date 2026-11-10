"""
Idempotent DYABROS catalogue importer.
Run from the backend directory with the project's virtualenv activated:
    python scripts/import_catalogue.py

The JSON file must be beside this script as:
    dyabros_catalogue_import.json
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.extensions import get_db


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "dyabros_catalogue_import.json"
IMPORT_SOURCE = "website_product_and_variety_data.xlsx"


def main():
    with DATA_FILE.open("r", encoding="utf-8") as file:
        products = json.load(file)

    app = create_app()

    with app.app_context():
        db = get_db()
        inserted = 0
        already_present = 0

        for item in products:
            now = datetime.now(timezone.utc)
            document = {
                **item,
                "is_active": True,
                "created_by": "excel_import",
                "import_source": IMPORT_SOURCE,
                "created_at": now,
                "updated_at": now,
            }

            result = db.products.update_one(
                {"sku": item["sku"]},
                {"$setOnInsert": document},
                upsert=True,
            )

            if result.upserted_id:
                inserted += 1
            else:
                already_present += 1

        print("DYABROS catalogue import finished.")
        print(f"Rows in import file: {len(products)}")
        print(f"New products inserted: {inserted}")
        print(f"Existing SKUs skipped: {already_present}")
        print(f"Total active products: {db.products.count_documents({'is_active': True})}")
        print("Existing products and manually entered values were not overwritten.")


if __name__ == "__main__":
    main()
