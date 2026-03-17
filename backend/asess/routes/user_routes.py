from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from asess.core.database import SessionLocal
from asess.schemas.user import UserCreate, UserRead, UserUpdate, Token
from asess.services import user_service
from asess.models.user import User
from asess.core.security import create_tokens
from asess.core.dependencies import get_current_user, check_admin
from typing import List

router = APIRouter()

FRONTEND_DIR = "/app/frontend"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/register")
def register_page():
    return FileResponse(f"{FRONTEND_DIR}/register.html", media_type="text/html")

@router.post("/register", response_model=UserRead)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    return user_service.create_user(db, user_in)

@router.get("/login")
def login_page():
    return FileResponse(f"{FRONTEND_DIR}/login.html", media_type="text/html")

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = user_service.authenticate(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token, refresh_token = create_tokens(user.email, user.role)
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)):
    """Return info for the currently authenticated user."""
    return current_user

@router.get("/dashboard")
def dashboard_page():
    return FileResponse(f"{FRONTEND_DIR}/dashboard.html", media_type="text/html")


# ===== Admin CRUD Endpoints =====

@router.get("/admin/users", response_model=List[UserRead])
def list_all_users(
    admin: User = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """List all users (admin only)."""
    return db.query(User).order_by(User.id).all()

@router.put("/admin/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    admin: User = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """Update a user's role or active status (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_update.role is not None:
        user.role = user_update.role
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    
    db.commit()
    db.refresh(user)
    return user

@router.delete("/admin/users/{user_id}")
def delete_user(
    user_id: int,
    admin: User = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    db.delete(user)
    db.commit()
    return {"detail": "User deleted successfully"}
