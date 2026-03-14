import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import asyncio
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from dotenv import load_dotenv

from lib.database import DatabaseManager, get_db
from schemas import TokenData, UserInDB

load_dotenv()

secret_key = os.getenv("SECRET_KEY")
algorithm = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

if not secret_key or len(secret_key) < 32:
    raise RuntimeError("secret_key is missing or too short. use at least 32 characters.")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """creates a new jwt access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt

def _decode_token(token: str) -> Optional[str]:
    """helper to decode jwt and extract sub (username)."""
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload.get("sub")
    except JWTError:
        return None

def get_current_user(token: str = Depends(oauth2_scheme), db: DatabaseManager = Depends(get_db)):
    """
    decodes token, extracts username, and retrieves user from db.
    this is a dependency for protected endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    username = _decode_token(token)
    if not username:
        raise credentials_exception
    
    user = db.getUserByUsername(username=username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_user_from_websocket(token: str):
    """
    similar to get_current_user, but for websockets where the token
    is passed as a query parameter.
    """
    if not token:
        return None
    
    username = _decode_token(token)
    if not username:
        return None
    
    db = DatabaseManager(auto_connect=False)
    await db.connect_async()
    try:
        user = await asyncio.to_thread(db.getUserByUsername, username)
        if user is None:
            return None

        return user
    finally:
        db.close()