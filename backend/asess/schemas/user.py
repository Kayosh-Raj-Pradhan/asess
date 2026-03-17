from pydantic import BaseModel, EmailStr, Field, validator
from typing import Literal
import re

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=20)
    full_name: str | None = None

    @validator('username')
    def username_message(cls, v):
        if len(v) < 3:
            raise ValueError('Username must have at least 3 characters')
        if len(v) > 20:
            raise ValueError('Username must not exceed 20 characters')
        return v

class UserCreate(UserBase):
    password: str
    role: Literal["doctor", "staff", "admin"] = "staff"

    @validator('password')
    def password_complexity(cls, v):
        if len(v) < 8:
            raise ValueError('Password must have at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v

class UserRead(UserBase):
    id: int
    role: str
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserUpdate(BaseModel):
    role: Literal["doctor", "staff", "admin"] | None = None
    is_active: bool | None = None