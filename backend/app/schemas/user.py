import uuid
from typing import Optional, Union
from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    employee_id: Optional[str] = None
    department: Optional[str] = "Drilling Operations & eRTMAC Division"
    role: Optional[str] = "DRILLING_ENGINEER"
    password: str
    confirm_password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: Union[str, uuid.UUID]
    full_name: str
    email: EmailStr
    employee_id: Optional[str] = None
    department: Optional[str] = "Drilling Operations & eRTMAC Division"
    role: str = "DRILLING_ENGINEER"

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    expires_in: Optional[int] = 3600

class TokenData(BaseModel):
    email: Optional[str] = None
    sub: Optional[str] = None
