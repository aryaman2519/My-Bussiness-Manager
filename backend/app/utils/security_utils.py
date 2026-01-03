import secrets
import string

def generate_security_code(length: int = 8) -> str:
    """
    Generate a secure random numeric string of fixed length.
    Ensures high entropy and allows leading zeros.
    """
    return ''.join(secrets.choice(string.digits) for _ in range(length))
