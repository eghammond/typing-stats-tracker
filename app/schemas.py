from pydantic import BaseModel, EmailStr, ConfigDict, Field
from datetime import datetime

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=8, max_length=72)
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class LoginCreate(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str

class ResultCreate(BaseModel):
    wpm: float
    accuracy: float
    duration: float

class ResultResponse(BaseModel):
    id: int
    user_id: int
    wpm: float
    accuracy: float
    duration: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class StatsResponse(BaseModel):
    avg_wpm: float
    best_wpm: float
    avg_accuracy: float
    total_tests: int
    model_config = ConfigDict(from_attributes=True)
    



