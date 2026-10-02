import uuid
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.user import Profile
from backend.app.models.audit import AuditLog
from backend.app.schemas.user import UserRegister, UserLogin, UserOut, Token
from backend.app.services.auth_service import get_current_user
from backend.app.utils.logger import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserOut)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    if user_in.password != user_in.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")

    # Call Supabase Auth signup
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    signup_payload = {
        "email": user_in.email,
        "password": user_in.password,
        "data": {
            "full_name": user_in.full_name,
            "employee_id": user_in.employee_id,
            "department": user_in.department or "Drilling Operations & eRTMAC Division",
            "role": user_in.role or "DRILLING_ENGINEER"
        }
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(f"{settings.SUPABASE_URL}/auth/v1/signup", headers=headers, json=signup_payload)
            if resp.status_code not in (200, 201):
                err = resp.json().get("msg") or resp.json().get("error_description") or "Registration failed."
                raise HTTPException(status_code=400, detail=err)

            data = resp.json()
            user_id = uuid.UUID(data["id"])
    except httpx.RequestError as e:
        logger.error(f"Supabase registration error: {e}")
        raise HTTPException(status_code=503, detail="Supabase authentication service unavailable.")

    # Ensure profile exists in public.profiles
    profile = db.query(Profile).filter(Profile.id == user_id).first()
    if not profile:
        profile = Profile(
            id=user_id,
            full_name=user_in.full_name,
            email=user_in.email,
            employee_id=user_in.employee_id,
            department=user_in.department or "Drilling Operations & eRTMAC Division",
            role=user_in.role or "DRILLING_ENGINEER"
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    audit = AuditLog(
        user_id=profile.id,
        user_email=profile.email,
        action="USER_REGISTER",
        resource=f"user:{profile.id}",
        details={"name": profile.full_name, "role": profile.role}
    )
    db.add(audit)
    db.commit()

    return profile


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "email": login_data.email,
        "password": login_data.password
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password", headers=headers, json=payload)
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password."
                )
            token_resp = resp.json()
            access_token = token_resp["access_token"]
            user_id = uuid.UUID(token_resp["user"]["id"])
            expires_in = token_resp.get("expires_in", 3600)
    except httpx.RequestError as e:
        logger.error(f"Supabase login error: {e}")
        raise HTTPException(status_code=503, detail="Supabase authentication service unavailable.")

    # Fetch Profile
    profile = db.query(Profile).filter(Profile.id == user_id).first()
    if not profile:
        meta = token_resp["user"].get("user_metadata", {})
        profile = Profile(
            id=user_id,
            full_name=meta.get("full_name", login_data.email.split("@")[0]),
            email=login_data.email,
            employee_id=meta.get("employee_id"),
            department=meta.get("department", "Drilling Operations & eRTMAC Division"),
            role=meta.get("role", "DRILLING_ENGINEER")
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    audit = AuditLog(
        user_id=profile.id,
        user_email=profile.email,
        action="LOGIN",
        resource=f"user:{profile.id}",
        details={"login": "SUCCESS"}
    )
    db.add(audit)
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": profile,
        "expires_in": expires_in
    }


@router.get("/me", response_model=UserOut)
def get_me(current_user: Profile = Depends(get_current_user)):
    return current_user


@router.post("/logout")
def logout(current_user: Profile = Depends(get_current_user), db: Session = Depends(get_db)):
    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        action="LOGOUT",
        resource=f"user:{current_user.id}"
    )
    db.add(audit)
    db.commit()
    return {"status": "SUCCESS", "message": "Logged out successfully."}
