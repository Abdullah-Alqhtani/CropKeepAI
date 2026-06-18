from pydantic import BaseModel

from app.models import UserRole


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: UserRole = UserRole.farmer


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
