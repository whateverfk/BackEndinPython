from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.Models.user import User
from app.core.security import decode_jwt
from app.db.session import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
) -> User:
    """
    Tương đương [Authorize]
    Header: Authorization: Bearer <token>
    """

    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authorization header không hợp lệ")

    token = authorization.split(" ")[1]
    payload = decode_jwt(token)

    user = db.query(User).filter(
        User.id == payload["sub"],
        User.is_active == True
    ).first()

    if not user:
        raise HTTPException(401, "User không tồn tại")

    return user
