
from app.extensions import get_db


# --------------------------------------------------
# DATABASE COLLECTIONS
# --------------------------------------------------

COLLECTIONS = [
    "admins",
    "dealers",
    "products",
    "categories",
    "orders",
    "invoices",
    "settings",
]


# --------------------------------------------------
# DATABASE INDEXES
# --------------------------------------------------

def create_indexes(db):
    """
    Create indexes for all DYABROS collections.

    MongoDB automatically creates a collection when
    an index is created on a collection that does
    not already exist.
    """

    # ADMIN INDEXES
    db.admins.create_index(
        [("email", 1)],
        unique=True,
        name="unique_admin_email"
    )

    # DEALER INDEXES
    db.dealers.create_index(
        [("dealer_id", 1)],
        unique=True,
        name="unique_dealer_id"
    )

    db.dealers.create_index(
        [("email", 1)],
        unique=True,
        sparse=True,
        name="unique_dealer_email"
    )

    db.dealers.create_index(
        [("phone", 1)],
        name="dealer_phone_lookup"
    )

    # PRODUCT INDEXES
    db.products.create_index(
        [("sku", 1)],
        unique=True,
        name="unique_product_sku"
    )

    db.products.create_index(
        [("category", 1)],
        name="product_category_lookup"
    )

    db.products.create_index(
        [("is_active", 1)],
        name="product_active_lookup"
    )

    # CATEGORY INDEXES
    db.categories.create_index(
        [("slug", 1)],
        unique=True,
        name="unique_category_slug"
    )

    # ORDER INDEXES
    db.orders.create_index(
        [("order_number", 1)],
        unique=True,
        name="unique_order_number"
    )

    db.orders.create_index(
        [
            ("dealer_id", 1),
            ("created_at", -1)
        ],
        name="dealer_order_history"
    )

    db.orders.create_index(
        [
            ("status", 1),
            ("created_at", -1)
        ],
        name="order_status_lookup"
    )

    # INVOICE INDEXES
    db.invoices.create_index(
        [("invoice_number", 1)],
        unique=True,
        name="unique_invoice_number"
    )

    db.invoices.create_index(
        [("order_id", 1)],
        unique=True,
        name="unique_invoice_order"
    )

    # SETTINGS INDEXES
    db.settings.create_index(
        [("key", 1)],
        unique=True,
        name="unique_setting_key"
    )


# --------------------------------------------------
# DATABASE INITIALIZATION
# --------------------------------------------------

def initialize_database():
    """
    Initialize DYABROS collections and indexes.
    Safe to execute repeatedly.
    """

    db = get_db()

    create_indexes(db)

    existing_collections = set(db.list_collection_names())

    return {
        "database": db.name,
        "collections": sorted(existing_collections),
        "total_collections": len(existing_collections),
        "indexes_created": True,
    }
