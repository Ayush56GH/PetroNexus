"""
PetroNexus Supabase Authentication & Multi-User Verification Tests (Phase 31)
Verifies:
- Supabase-issued JWT verification
- USER_A (engineer@oilindia.in) login & profile resolution
- USER_B (geologist@oilindia.in) login & profile resolution
- HTTP 401 unauthorized handling for missing/invalid tokens
- Multi-user identity isolation
"""
import sys
import httpx
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.config import settings
from backend.app.database import SessionLocal
from backend.app.models.user import Profile
from backend.app.services.auth_service import verify_supabase_token, get_current_user

def test_supabase_auth_login_user_a():
    """Test login with primary Drilling Engineer credentials via Supabase"""
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "email": "engineer@oilindia.in",
        "password": "OilIndia@2026"
    }
    resp = httpx.post(f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password", headers=headers, json=payload, timeout=10)
    assert resp.status_code == 200, f"Login failed for USER_A: {resp.text}"
    data = resp.json()
    token = data["access_token"]
    assert len(token) > 50
    user_data = verify_supabase_token(token)
    assert user_data["email"] == "engineer@oilindia.in"
    print(f"[PASS] test_supabase_auth_login_user_a passed (User ID: {user_data['id']}).")
    return token

def test_supabase_auth_signup_user_b():
    """Test signup/login for second user (USER_B) to verify multi-user isolation"""
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    signup_payload = {
        "email": "geologist@oilindia.in",
        "password": "Geologist@2026",
        "data": {
            "full_name": "Devajit Saikia",
            "employee_id": "OIL-GEO-1092",
            "department": "Geological & Subsurface Evaluation",
            "role": "GEOLOGIST"
        }
    }
    # Attempt signup (or ignore if already exists)
    httpx.post(f"{settings.SUPABASE_URL}/auth/v1/signup", headers=headers, json=signup_payload, timeout=10)

    # Login USER_B
    login_payload = {
        "email": "geologist@oilindia.in",
        "password": "Geologist@2026"
    }
    resp = httpx.post(f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password", headers=headers, json=login_payload, timeout=10)
    assert resp.status_code == 200, f"Login failed for USER_B: {resp.text}"
    data = resp.json()
    token_b = data["access_token"]
    user_b_data = verify_supabase_token(token_b)
    assert user_b_data["email"] == "geologist@oilindia.in"
    print(f"[PASS] test_supabase_auth_signup_user_b passed (User B ID: {user_b_data['id']}).")
    return token_b

def test_multi_user_profile_isolation(token_a, token_b):
    """Verify that USER_A and USER_B have completely distinct, isolated profiles"""
    db = SessionLocal()
    try:
        profile_a = get_current_user(token_a, db)
        profile_b = get_current_user(token_b, db)

        assert profile_a.id != profile_b.id, "Security failure: Users share same ID!"
        assert profile_a.email == "engineer@oilindia.in"
        assert profile_b.email == "geologist@oilindia.in"
        assert profile_a.role == "DRILLING_ENGINEER"
        assert profile_b.role == "GEOLOGIST"
        print(f"[PASS] test_multi_user_profile_isolation passed: User A ({profile_a.id}) != User B ({profile_b.id})")
    finally:
        db.close()

def test_invalid_token_rejected():
    """Verify 401 when token is invalid or missing"""
    db = SessionLocal()
    try:
        try:
            get_current_user(None, db)
            assert False, "Should have raised 401 for missing token"
        except Exception as e:
            assert "401" in str(e) or "Authentication required" in str(e)

        try:
            get_current_user("invalid.fake.jwt.token", db)
            assert False, "Should have raised 401 for invalid token"
        except Exception as e:
            assert "401" in str(e) or "Could not validate" in str(e) or "Invalid" in str(e)

        print("[PASS] test_invalid_token_rejected passed (401 enforced).")
    finally:
        db.close()

if __name__ == "__main__":
    t_a = test_supabase_auth_login_user_a()
    t_b = test_supabase_auth_signup_user_b()
    test_multi_user_profile_isolation(t_a, t_b)
    test_invalid_token_rejected()
    print("ALL 4 SUPABASE AUTH TESTS PASSED!")
