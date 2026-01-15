from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.auth import RegisterDto, LoginDto, ChangePasswordDto
from app.Models.user import User
from app.api.deps import get_db, get_current_user, CurrentUser
from app.core.security import create_jwt, hash_password, verify_password
from app.core.constants import (
    ERROR_MSG_USERNAME_EXISTS,
    ERROR_MSG_INVALID_CREDENTIALS,
    ERROR_MSG_USER_NOT_FOUND,
    ERROR_MSG_OLD_PASSWORD_INCORRECT
)

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register")
def register(dto: RegisterDto, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == dto.username).first():
        raise HTTPException(400, ERROR_MSG_USERNAME_EXISTS)

    user = User(
        username=dto.username,
        password_hash=hash_password(dto.password),
        role="SuperAdmin",
        is_active=True
    )

   
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"token": create_jwt(user)}


@router.post("/login")
def login(dto: LoginDto, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.username == dto.username,
        User.is_active == True
    ).first()

    if not user or not verify_password(dto.password, user.password_hash):
        raise HTTPException(401, ERROR_MSG_INVALID_CREDENTIALS)

    return {"token": create_jwt(user)}


@router.post("/change-password")
def change_password(
    dto: ChangePasswordDto,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.id == current_user.user_id,
        User.is_active == True
    ).first()

    if not user:
        raise HTTPException(404, ERROR_MSG_USER_NOT_FOUND)

    if not verify_password(dto.old_password, user.password_hash):
        raise HTTPException(400, ERROR_MSG_OLD_PASSWORD_INCORRECT)

    user.password_hash = hash_password(dto.new_password)
    db.commit()

    return {"message": "Password updated"}

