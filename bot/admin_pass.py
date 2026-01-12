import os
import json
import time
import string
import secrets

PASS_FILE = os.path.join(os.path.dirname(__file__), "..", ".admin_pass.json")
PASSWORD_VALID_SECONDS = 120  # 2 minutes


def _load() -> dict:
    try:
        if os.path.exists(PASS_FILE):
            with open(PASS_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {"password": None, "created_at": 0}


def _save(data: dict):
    try:
        with open(PASS_FILE, 'w') as f:
            json.dump(data, f)
    except:
        pass


def generate_admin_password() -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(8))


def get_or_create_password() -> tuple[str, int]:
    """Returns (password, remaining_seconds)"""
    data = _load()
    now = time.time()
    elapsed = now - data["created_at"]
    
    if data["password"] and elapsed < PASSWORD_VALID_SECONDS:
        remaining = int(PASSWORD_VALID_SECONDS - elapsed)
        return data["password"], remaining
    
    # Generate new password
    new_pass = generate_admin_password()
    _save({"password": new_pass, "created_at": now})
    return new_pass, PASSWORD_VALID_SECONDS


def verify_password(password: str) -> bool:
    """Verify password is valid and not expired"""
    data = _load()
    
    if not data["password"]:
        return False
    
    elapsed = time.time() - data["created_at"]
    if elapsed > PASSWORD_VALID_SECONDS:
        return False
    
    return password == data["password"]
