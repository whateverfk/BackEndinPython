
from sqlalchemy.orm import Session
from typing import Optional
from app.Models.user import User
from app.core.security import decode_jwt
from app.db.session import SessionLocal
from uuid import UUID
from fastapi import Header, Depends, HTTPException, status
from app.db.session import get_db



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



class CurrentUser:
    def __init__(self, payload: dict):
        self.user_id = UUID(payload[
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier"
        ])
        self.role = payload[
            "http://schemas.microsoft.com/ws/2008/06/identity/claims/role"
        ]
        self.superadmin_id = UUID(payload["superAdminId"])


def get_current_user(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db)
) -> CurrentUser:

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing Authorization")

    token = authorization.split(" ")[1]
    payload = decode_jwt(token)

    user = db.query(User).filter(
        User.id == payload[
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier"
        ],
        User.is_active == True
    ).first()

    if not user:
        raise HTTPException(401, "User not found")

    return CurrentUser(payload)

