
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from app.config import Config
from app.extensions import init_mongodb
from app.database import initialize_database
from app.routes.health import health_bp
from app.routes.auth import auth_bp
from app.routes.products import products_bp
from app.routes.orders import orders_bp
from app.routes.dealers import dealers_bp
from app.routes.invoices import invoices_bp


def create_app():
    """
    Create and configure the DYABROS Flask application.
    """

    app = Flask(__name__)

    # Load application configuration
    Config.validate()
    app.config.from_object(Config)

    # Configure CORS
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": app.config["FRONTEND_ORIGINS"]
            }
        }
    )

    # Initialize JWT
    JWTManager(app)

    # Initialize MongoDB connection
    init_mongodb(app)

    # Initialize database collections and indexes
    database_info = initialize_database()

    app.logger.info(
        "DYABROS database initialized: %s",
        database_info
    )

    # Register routes
    app.register_blueprint(health_bp)

    app.register_blueprint(auth_bp)

    app.register_blueprint(products_bp)

    app.register_blueprint(orders_bp)

    app.register_blueprint(dealers_bp)

    app.register_blueprint(invoices_bp)

    return app
