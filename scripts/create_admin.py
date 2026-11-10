import sys
from pathlib import Path
import getpass

# Add the backend directory to Python's import path.
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app import create_app
from app.models import Admin


def main():
    app = create_app()

    with app.app_context():
        print("\n--- DYABROS Admin Setup ---")

        name = input("Admin name: ").strip()
        email = input("Admin email: ").strip().lower()

        password = getpass.getpass("Admin password (minimum 12 characters): ")
        confirm_password = getpass.getpass("Confirm password: ")

        if password != confirm_password:
            print("Error: Passwords do not match.")
            return

        try:
            admin_id = Admin.create(
                name=name,
                email=email,
                password=password
            )
            print("\nAdmin created successfully.")
            print("Admin ID:", admin_id)

        except ValueError as error:
            print("Error:", error)


if __name__ == "__main__":
    main()