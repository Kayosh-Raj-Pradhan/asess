from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from asess.models.user import User
from asess.schemas.user import UserCreate
from asess.core.security import hash_password, verify_password

def create_user(db: Session, user_in: UserCreate) -> User:
    # Check if email or username exists
    user_exists = db.query(User).filter(
        (User.email == user_in.email) | (User.username == user_in.username)
    ).first()
    
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or Email already registered"
        )

    new_user = User(
        email=user_in.email,
        username=user_in.username,
        full_name=user_in.full_name,
        hashed_password=hash_password(user_in.password),
        role=user_in.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def authenticate(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User is inactive")
    return user