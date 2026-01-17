from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from fastapi import Header, Depends, HTTPException, status

from app.Models.user import User
from app.core.security import decode_jwt
from app.db.session import get_db
from app.core.constants import (
    JWT_CLAIM_NAME_ID,
    JWT_CLAIM_ROLE,
    JWT_CLAIM_SUPERADMIN_ID,
    ERROR_MSG_MISSING_AUTH,
    ERROR_MSG_USER_NOT_FOUND
)


class CurrentUser:
    """
    Represents the currently authenticated user from JWT token.
    
    This class extracts and provides easy access to user claims from the JWT payload.
    """
    
    def __init__(self, payload: dict):
        self.user_id: str = payload[JWT_CLAIM_NAME_ID]
        self.role: str = payload[JWT_CLAIM_ROLE]
        self.superadmin_id: str | None = payload.get(JWT_CLAIM_SUPERADMIN_ID)


def get_current_user(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db)
) -> CurrentUser:
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, ERROR_MSG_MISSING_AUTH)

    token = authorization.split(" ")[1]
    payload = decode_jwt(token)

    user = db.query(User).filter(
        User.id == payload[JWT_CLAIM_NAME_ID],
        User.is_active == True
    ).first()

    if not user:
        raise HTTPException(401, ERROR_MSG_USER_NOT_FOUND)

    return CurrentUser(payload)

def check_role(user: CurrentUser, required_role: str):
    if user.role != required_role:
        raise HTTPException(
            status_code=403,
            detail=f"This required role: {required_role}"
        )