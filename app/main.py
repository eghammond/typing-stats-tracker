from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session
from .database import get_db, engine
from .models import User, Result
from .schemas import UserCreate, UserResponse, LoginCreate, LoginResponse, ResultCreate, ResultResponse, StatsResponse
from . import models
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import jwt, JWTError, ExpiredSignatureError
from dotenv import load_dotenv
import os
from fastapi.security import OAuth2PasswordBearer
from typing import List
from datetime import datetime, timedelta, timezone
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from fastapi.middleware.cors import CORSMiddleware

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

ph = PasswordHasher()

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

limiter = Limiter(key_func = get_remote_address)

app = FastAPI()
models.Base.metadata.create_all(bind=engine)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"]
)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    return user


# POST /auth/register
@app.post("/auth/register", response_model=UserResponse)
@limiter.limit("5/minute")
def create_user(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user is not None:
        raise HTTPException(status_code=400, detail="Username already exists")
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user is not None:
        raise HTTPException(status_code=400, detail="Email already exists")
    new_user = User(username = user.username, email = user.email, password = ph.hash(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# POST /auth/login
@app.post("/auth/login", response_model=LoginResponse)
@limiter.limit("5/minute")
def create_login(request: Request, login: LoginCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login.username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    try:
        ph.verify(user.password, login.password)
    except VerifyMismatchError:
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    payload = {"sub": str(user.id), "exp": datetime.now(timezone.utc) + timedelta(minutes=30)}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return LoginResponse(access_token=token, token_type="bearer")

# POST /results
@app.post("/results", response_model=ResultResponse)
@limiter.limit("10/minute")
def create_result(request: Request, result: ResultCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_result = Result(user_id = user.id, wpm = result.wpm, accuracy = result.accuracy, duration = result.duration)
    db.add(new_result)
    db.commit()
    db.refresh(new_result)
    return new_result

# GET /results

@app.get("/results", response_model=List[ResultResponse])
@limiter.limit("5/minute")
def return_results(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    results = db.query(Result).filter(Result.user_id == user.id).all()
    return results

# GET /results/stats
@app.get("/results/stats", response_model=StatsResponse)
@limiter.limit("5/minute")
def return_stats(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    avg_wpm, best_wpm, avg_accuracy, total_tests = db.query(
        func.avg(Result.wpm),
        func.max(Result.wpm),
        func.avg(Result.accuracy),
        func.count(Result.id)
    ).filter(Result.user_id == user.id).one()
    if total_tests == 0:
        avg_wpm, best_wpm, avg_accuracy, total_tests = 0, 0, 0, 0
    stats_response = StatsResponse(avg_wpm = avg_wpm, best_wpm = best_wpm, avg_accuracy = avg_accuracy, total_tests = total_tests)
    return stats_response
    
        

