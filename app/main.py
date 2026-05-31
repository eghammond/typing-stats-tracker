from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db, engine
from .models import User
from .schemas import UserCreate, UserResponse, LoginCreate, LoginResponse
from . import models
from passlib.hash import bcrypt
from jose import jwt
from dotenv import load_dotenv
import os

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

# POST /auth/register
@app.post("/auth/register", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = User(username = user.username, email = user.email, password = bcrypt.hash(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# POST /auth/login
@app.post("/auth/login", response_model=LoginResponse)
def create_login(login: LoginCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login.username).first()
    if user is None or not bcrypt.verify(login.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    payload = {"sub": str(user.id)}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return LoginResponse(access_token=token, token_type="bearer")
    
        

