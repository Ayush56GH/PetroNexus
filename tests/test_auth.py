"""
PetroNexus Authentication Tests
Verifies user registration, password verification with bcrypt, JWT creation and login.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.database import SessionLocal
from backend.app.models.user import User
from backend.app.services.auth_service import verify_password, get_password_hash, create_access_token

def test_password_hashing():
    raw = "OilIndia@2026"
    hashed = get_password_hash(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False
    print("[PASS] test_password_hashing passed.")

def test_jwt_token():
    token = create_access_token(data={"sub": "engineer@oilindia.in", "role": "DRILLING_ENGINEER"})
    assert isinstance(token, str)
    assert len(token) > 20
    print("[PASS] test_jwt_token passed.")

def test_demo_user_exists():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "engineer@oilindia.in").first()
        assert user is not None
        assert user.role == "DRILLING_ENGINEER"
        print(f"[PASS] test_demo_user_exists passed ({user.full_name}, {user.employee_id}).")
    finally:
        db.close()

if __name__ == "__main__":
    test_password_hashing()
    test_jwt_token()
    test_demo_user_exists()
    print("All Auth tests passed successfully!")
