from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.auth import RegisterDto, LoginDto, TokenResponse
from app.Models.user import User
from app.db.session import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_jwt
)

router = APIRouter(prefix="/api/auth", tags=["Auth"])

# Register → SuperAdmin
@router.post("/register", response_model=TokenResponse)
def register(dto: RegisterDto, db: Session = Depends(get_db)):

    if db.query(User).filter(User.username == dto.username).first():
        raise HTTPException(status_code=400, detail="Username đã tồn tại")

    user = User(
        username=dto.username,
        password_hash=hash_password(dto.password),
        role="SuperAdmin",
        is_active=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_jwt(
        str(user.id),
        user.username,
        user.role
    )

    return {"token": token}


# Login
@router.post("/login", response_model=TokenResponse)
def login(dto: LoginDto, db: Session = Depends(get_db)):

    user = db.query(User).filter(
        User.username == dto.username,
        User.is_active == True
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Tài khoản không hợp lệ")

    if not verify_password(dto.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Sai mật khẩu")

    token = create_jwt(
        str(user.id),
        user.username,
        user.role
    )

    return {"token": token}
