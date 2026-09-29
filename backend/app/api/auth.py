from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.audit import AuditLog
from backend.app.schemas.user import UserRegister, UserLogin, UserOut, Token
from backend.app.services.auth_service import verify_password, get_password_hash, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserOut)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    if user_in.password != user_in.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")
    
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email is already registered.")

    existing_emp = db.query(User).filter(User.employee_id == user_in.employee_id).first()
    if existing_emp:
        raise HTTPException(status_code=400, detail="Employee ID is already registered.")

    user = User(
        full_name=user_in.full_name,
        email=user_in.email,
        employee_id=user_in.employee_id,
        department=user_in.department or "Drilling Operations",
        hashed_password=get_password_hash(user_in.password),
        role="DRILLING_ENGINEER",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Audit log
    audit = AuditLog(
        user_id=user.id,
        user_email=user.email,
        action="USER_REGISTER",
        resource=f"user:{user.id}",
        details={"name": user.full_name, "role": user.role}
    )
    db.add(audit)
    db.commit()

    return user

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    access_token = create_access_token(data={"sub": user.email, "role": user.role})

    audit = AuditLog(
        user_id=user.id,
        user_email=user.email,
        action="LOGIN",
        resource=f"user:{user.id}",
        details={"login": "SUCCESS"}
    )
    db.add(audit)
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        action="LOGOUT",
        resource=f"user:{current_user.id}"
    )
    db.add(audit)
    db.commit()
    return {"status": "SUCCESS", "message": "Logged out successfully."}
