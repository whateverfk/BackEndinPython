from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from dotenv import load_dotenv
import os
import jwt

from app.core.constants import (
    JWT_CLAIM_NAME,
    JWT_CLAIM_NAME_ID,
    JWT_CLAIM_ROLE,
    JWT_CLAIM_SUPERADMIN_ID,
    JWT_ALGORITHM,
    JWT_EXPIRE_MINUTES,
    ERROR_MSG_TOKEN_EXPIRED,
    ERROR_MSG_INVALID_TOKEN
)

load_dotenv("./app/.env")

SECRET_KEY = os.getenv("SECRET_KEY")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hash: str) -> bool:
    return pwd_context.verify(password, hash)


def create_jwt(user) -> str:
    payload = {
        JWT_CLAIM_NAME: user.username,
        JWT_CLAIM_NAME_ID: str(user.id),
        JWT_CLAIM_ROLE: user.role,

        # LOGIC QUAN TRỌNG
        JWT_CLAIM_SUPERADMIN_ID: str(
            user.id if user.role == "SuperAdmin"
            else user.owner_superadmin_id
        ),

        "exp": datetime.now().astimezone() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    }
    
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, ERROR_MSG_TOKEN_EXPIRED)
    except jwt.InvalidTokenError:
        raise HTTPException(401, ERROR_MSG_INVALID_TOKEN)

