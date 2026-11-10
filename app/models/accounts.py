from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password: str) -> str:
    """Create a secure hash from a plain-text password."""
    if not password or not password.strip():
        raise ValueError("Password cannot be empty.")

    return generate_password_hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """Verify a password against its stored hash."""
    if not password_hash or not password:
        return False

    return check_password_hash(password_hash, password)