from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    uuid: str
    username: str
    realname: str
    email: Optional[str] = None
    role: str
    regdate: Optional[int] = None

class CreateUserRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role: str = "player"

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class ResetRequest(BaseModel):
    username: str

class ResetRequestResponse(BaseModel):
    username: str
    status: str
    requested_at: str

class RoleChangeRequest(BaseModel):
    role: str
