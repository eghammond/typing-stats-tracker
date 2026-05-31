from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from .database import get_db, engine
from .models import User, Result
from .schemas import UserCreate, UserResponse, LoginCreate, LoginResponse, ResultCreate, ResultResponse, StatsResponse
from . import models
from passlib.hash import bcrypt
from jose import jwt, JWTError
from dotenv import load_dotenv
import os
from fastapi.security import OAuth2PasswordBearer
from typing import List

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    return user


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

# POST /results
@app.post("/results", response_model=ResultResponse)
def create_result(result: ResultCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_result = Result(user_id = user.id, wpm = result.wpm, accuracy = result.accuracy, duration = result.duration)
    db.add(new_result)
    db.commit()
    db.refresh(new_result)
    return new_result

# GET /results

@app.get("/results", response_model=List[ResultResponse])
def return_results(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    results = db.query(Result).filter(Result.user_id == user.id).all()
    return results

# GET /results/stats
@app.get("/results/stats", response_model=StatsResponse)
def return_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    avg_wpm, best_wpm, avg_accuracy, total_tests = db.query(
        func.avg(Result.wpm),
        func.max(Result.wpm),
        func.avg(Result.accuracy),
        func.count(Result.id)
    ).filter(Result.user_id == user.id).one()
    if total_tests == 0:
        raise HTTPException(status_code = 404, detail = "No results found")
    stats_response = StatsResponse(avg_wpm = avg_wpm, best_wpm = best_wpm, avg_accuracy = avg_accuracy, total_tests = total_tests)
    return stats_response
    
        

