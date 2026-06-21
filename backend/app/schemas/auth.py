from pydantic import BaseModel, Field

from app.models import UserRole


class AdminCreateUserRequest(BaseModel):
    name: str
    email: str
    password: str = Field(min_length=8)
    role: UserRole = UserRole.farmer


class LoginRequest(BaseModel):
    email: str
    password: str


class AdminUpdateUserRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class AdminResetPasswordRequest(BaseModel):
    password: str = Field(min_length=8)


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
