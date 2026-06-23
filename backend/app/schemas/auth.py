"""Describe the safe request and response shapes for authentication endpoints.

Pydantic validates incoming login/admin data and prevents password hashes from
being included in user responses sent to the frontend.
"""

from pydantic import BaseModel, Field

from app.models import UserRole


class AdminCreateUserRequest(BaseModel):
    # Admin-created passwords must meet the minimum length before hashing.
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
    # This public model intentionally excludes password_hash.
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
