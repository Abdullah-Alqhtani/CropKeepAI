"""Validate login credentials, JWTs, and role-based permissions.

Protected routes depend on these functions so authorization rules are written
once and applied consistently across the API.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import ALGORITHM, verify_password
from app.db.session import get_db
from app.models import User

# FastAPI extracts the Bearer token from the Authorization header using this scheme.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        return None
    return user


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    # Decode the signed JWT, then re-check the user in the database in case the account was disabled.
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except JWTError as exc:
        raise credentials_error from exc
    if not email:
        raise credentials_error
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise credentials_error
    return user


def require_roles(*roles: str):
    # Return a reusable dependency for routes such as admin-only user management.
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role.value not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return checker
