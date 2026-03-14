from fastapi import APIRouter, Depends, HTTPException, status
from lib.database import DatabaseManager, get_db
from schemas import User, UserCreate, UserInDB
from lib.password_manager import hashPassword
from api.auth import get_current_user

router = APIRouter()

@router.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED, tags=["Users"])
def create_user(user: UserCreate, db: DatabaseManager = Depends(get_db)):
    """creates a new user after checking if the username already exists."""
    db_user = db.getUserByUsername(user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="username already registered")

    hashed_password = hashPassword(user.password)
    new_user = db.createUser(user, hashed_password)
    if not new_user:
        raise HTTPException(status_code=500, detail="could not create user.")
    return new_user

@router.get("/users/me", response_model=User, tags=["Users"])
def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    """protected endpoint. returns the data of the currently authenticated user."""
    return current_user