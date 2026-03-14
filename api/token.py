from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from lib.password_manager import checkPassword

from api.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
)
from lib.database import DatabaseManager, get_db
from schemas import Token

router = APIRouter()

@router.post("/token", response_model=Token, tags=["Authentication"])
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: DatabaseManager = Depends(get_db)
):
    """login endpoint. receives username and password from a form."""
    user = db.getUserByUsername(form_data.username)

    if not user or not checkPassword(user.password_hash, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}