from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.auth import RegisterDto, LoginDto
from app.Models.user import User
from app.api.deps import get_db
from app.core.security import create_jwt, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register")
def register(dto: RegisterDto, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == dto.username).first():
        raise HTTPException(400, "Username exists")

    user = User(
        username=dto.username,
        password_hash=hash_password(dto.password),
        role="SuperAdmin",
        is_active=True
    )

    print(" DEBUG - User object before commit:", user.__dict__)
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
        raise HTTPException(401, "Invalid credentials")

    return {"token": create_jwt(user)}
