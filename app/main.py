from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from datetime import timedelta
import uvicorn
from sqlalchemy.orm import Session

import logging


from app.models.user import User
from app.database import Base, engine, get_db
from app.schemas.user import UserCreate, UserOut
from app.schemas.token import Token
from app.authorization.auth_user import (
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_password_hash,
    get_current_active_user
)


app = FastAPI()

Base.metadata.create_all(bind=engine)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



@app.post("/register", response_model=UserOut)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    if user_data.tg_id:
        db_user_tg = db.query(User).filter(User.tg_id == user_data.tg_id).first()
        if db_user_tg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telegram ID уже зарегестрирован"
            )

    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        surname=user_data.surname,
        hashed_password=hashed_password,
        tg_id=user_data.tg_id,
        disabled=user_data.disabled
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
) -> Token:
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"email": user.email},
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@app.get("/users/me", response_model=UserOut)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user


@app.get("/users/", response_model=list[UserOut])
async def get_users(
        db: Session = Depends(get_db)
):
    users = db.query(User).all()
    return users


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        reload=True
    )