from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from dotenv import load_dotenv
import os

load_dotenv("./app/.env")


SECRET_KEY = os.getenv("SECRET_KEY")
import jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


ALGORITHM = "HS256"
EXPIRE_MINUTES = 60 
CLAIM_NAME = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"
CLAIM_NAME_ID = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier"
CLAIM_ROLE = "http://schemas.microsoft.com/ws/2008/06/identity/claims/role"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hash: str) -> bool:
    return pwd_context.verify(password, hash)

def create_jwt(user) -> str:
    payload = {
        CLAIM_NAME: user.username,
        CLAIM_NAME_ID: str(user.id),
        CLAIM_ROLE: user.role,

        #  LOGIC QUAN TRỌNG
        "superAdminId": str(
            user.id if user.role == "SuperAdmin"
            else user.owner_superadmin_id
        ),

        "exp": datetime.now().astimezone() + timedelta(minutes=EXPIRE_MINUTES)
    }
    
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
