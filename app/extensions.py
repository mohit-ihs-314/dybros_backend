
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError


mongo_client = None
mongo_db = None


def init_mongodb(app):
    """
    Initialize MongoDB Atlas connection.
    """

    global mongo_client, mongo_db

    mongo_uri = app.config.get("MONGO_URI")
    database_name = app.config.get("MONGO_DB_NAME")

    if not mongo_uri:
        raise ValueError("MONGO_URI is not configured.")

    mongo_client = MongoClient(
        mongo_uri,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
        appname="DYABROS-Flask-Backend"
    )

    try:
        # Verify the MongoDB Atlas connection
        mongo_client.admin.command("ping")

        # Select DYABROS database
        mongo_db = mongo_client[database_name]

        app.logger.info(
            "Connected to MongoDB database: %s",
            database_name
        )

    except (ConnectionFailure, ServerSelectionTimeoutError):
        mongo_client.close()
        mongo_client = None
        mongo_db = None

        app.logger.exception("MongoDB connection failed.")
        raise


def get_db():
    """
    Return the active MongoDB database.
    """

    if mongo_db is None:
        raise RuntimeError("MongoDB is not initialized.")

    return mongo_db


def close_mongodb():
    """
    Close MongoDB connection.
    """

    global mongo_client, mongo_db

    if mongo_client:
        mongo_client.close()

    mongo_client = None
    mongo_db = None
