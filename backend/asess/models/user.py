from sqlalchemy import Column, Integer, String, Boolean
from asess.core.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False) # Added for your matching requirement
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default="user")  # "admin", "user", etc.
    is_active = Column(Boolean, default=True)