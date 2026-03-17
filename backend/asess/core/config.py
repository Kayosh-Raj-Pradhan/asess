# asess/core/config.py
import os

class Settings:
    # Change this to lowercase to match your database.py call
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+psycopg2://asessuser:asesspassword@db:5432/asess_db"
    )

settings = Settings()