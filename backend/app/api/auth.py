"""Define login and administrator-only user-management API endpoints.

The router uses database sessions and authentication dependencies to protect
user records, then returns safe response schemas to the frontend.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import ChatMessage, ChatSession, DiagnosisResult, ImageUpload, ProductRecommendation, User
from app.schemas.auth import (
    AdminCreateUserRequest,
    AdminResetPasswordRequest,
    AdminUpdateUserRequest,
    LoginRequest,
    TokenResponse,
    UserOut,
)
from app.services.auth_service import get_current_user, require_roles

router = APIRouter()


@router.get("/admin-check")
def admin_check(db: Session = Depends(get_db)):
    # This deployment check deliberately reports status only, never credentials.
    admin_email = settings.default_admin_email.strip().lower()
    users_count = db.query(User).count()
    default_admin_exists = bool(admin_email) and (
        db.query(User.id).filter(func.lower(User.email) == admin_email).first() is not None
    )
    return {
        "database_connected": True,
        "users_count": users_count,
        "default_admin_email_configured": bool(admin_email),
        "default_admin_exists": default_admin_exists,
    }


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    # Successful password verification creates a JWT that the frontend stores for later requests.
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is disabled. Contact an administrator.")
    token = create_access_token(user.email, user.role.value)
    return TokenResponse(access_token=token, user=user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: AdminCreateUserRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    # Only an authenticated admin can reach this route through require_roles().
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: AdminUpdateUserRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles("admin")),
):
    user = _get_user_or_404(db, user_id)
    if payload.email and payload.email != user.email:
        existing = db.query(User).filter(User.email == payload.email, User.id != user.id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
        user.email = payload.email
    if payload.name is not None:
        user.name = payload.name
    if payload.role is not None:
        if user.id == admin.id and payload.role.value != "admin":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admins cannot remove their own admin role")
        user.role = payload.role
    if payload.is_active is not None:
        if user.id == admin.id and payload.is_active is False:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admins cannot disable their own account")
        user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/reset-password", response_model=UserOut)
def reset_user_password(
    user_id: int,
    payload: AdminResetPasswordRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    user = _get_user_or_404(db, user_id)
    user.password_hash = hash_password(payload.password)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles("admin")),
):
    user = _get_user_or_404(db, user_id)
    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admins cannot delete their own account")
    diagnosis_ids = [item.id for item in db.query(DiagnosisResult.id).filter(DiagnosisResult.user_id == user.id).all()]
    session_ids = [item.id for item in db.query(ChatSession.id).filter(ChatSession.user_id == user.id).all()]
    if diagnosis_ids:
        db.query(ProductRecommendation).filter(ProductRecommendation.diagnosis_id.in_(diagnosis_ids)).delete(synchronize_session=False)
    if session_ids:
        db.query(ChatMessage).filter(ChatMessage.session_id.in_(session_ids)).delete(synchronize_session=False)
    db.query(ChatSession).filter(ChatSession.user_id == user.id).delete(synchronize_session=False)
    db.query(DiagnosisResult).filter(DiagnosisResult.user_id == user.id).delete(synchronize_session=False)
    db.query(ImageUpload).filter(ImageUpload.user_id == user.id).delete(synchronize_session=False)
    db.delete(user)
    db.commit()
    return None


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
