"""
PetroNexus Supabase Authentication & Multi-Tenant Authorization Service
Verifies Supabase-issued JWTs, enforces cryptographic user validation,
and maps identities to the public.profiles table. No local passwords stored.
"""
import time
import uuid
from typing import Optional, Dict, Any
import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.user import Profile
from backend.app.utils.logger import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False)

# Short-lived in-memory token cache (60 seconds) to reduce latency while preserving security
_TOKEN_CACHE: Dict[str, tuple[Dict[str, Any], float]] = {}

def verify_supabase_token(token: str) -> Dict[str, Any]:
    """
    Validates a Supabase-issued access token directly against Supabase Auth endpoint.
    Caches verified payloads for 60 seconds.
    """
    now = time.time()
    if token in _TOKEN_CACHE:
        cached_user, expire_at = _TOKEN_CACHE[token]
        if now < expire_at:
            return cached_user

    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase credentials are not configured on the server."
        )

    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {token}"
    }

    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.get(f"{settings.SUPABASE_URL}/auth/v1/user", headers=headers)
            if resp.status_code == 200:
                user_data = resp.json()
                _TOKEN_CACHE[token] = (user_data, now + 60.0)
                return user_data
            elif resp.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired session. Please log in again.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                logger.error(f"Supabase auth check returned {resp.status_code}: {resp.text}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials with Supabase.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
    except httpx.RequestError as e:
        logger.error(f"Supabase connection exception: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase Auth service is unreachable."
        )

def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Profile:
    """
    Derives authenticated identity strictly from the verified Supabase JWT.
    Enforces multi-user security boundaries.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_data = verify_supabase_token(token)
    user_id_str = user_data.get("id")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing user id.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject UUID format.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    profile = db.query(Profile).filter(Profile.id == user_uuid).first()
    if not profile:
        # Fallback profile creation if not triggered by DB
        meta = user_data.get("user_metadata", {})
        email = user_data.get("email", "")
        profile = Profile(
            id=user_uuid,
            full_name=meta.get("full_name", email.split("@")[0]),
            email=email,
            employee_id=meta.get("employee_id"),
            department=meta.get("department", "Drilling Operations & eRTMAC Division"),
            role=meta.get("role", "DRILLING_ENGINEER")
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return profile

def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[Profile]:
    """
    Returns authenticated user if valid token is provided, otherwise None without raising 401.
    Useful for endpoints serving public DEMO data while enhancing with user context if logged in.
    """
    if not token:
        return None
    try:
        return get_current_user(token, db)
    except HTTPException:
        return None
