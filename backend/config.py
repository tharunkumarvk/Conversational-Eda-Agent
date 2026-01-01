# backend/config.py
import os
from pydantic_settings import BaseSettings
from typing import List

# Ensure .env overrides system environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except Exception:
    pass

class Settings(BaseSettings):
    # API Configuration
    GOOGLE_API_KEY: str
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    ENVIRONMENT: str = "development"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_SECRET_KEY: str = "jwt-secret-key-change-in-production"  # For JWT tokens
    ALLOWED_ORIGINS: str = "*"
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""  # Get from Google Cloud Console
    GOOGLE_CLIENT_SECRET: str = ""  # Get from Google Cloud Console
    
    # Database
    DATABASE_URL: str = "sqlite:///./backend/eda_agent.db"  # Default to SQLite
    # For cloud DB, set in .env: DATABASE_URL=postgresql://user:pass@host:port/dbname
    
    # Supabase Storage (for cloud file storage)
    SUPABASE_URL: str = ""  # e.g., https://xxxxx.supabase.co
    SUPABASE_KEY: str = ""  # anon/public key from Supabase dashboard
    SUPABASE_BUCKET: str = "eda-files"  # Storage bucket name
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 104857600  # 100MB
    UPLOAD_DIR: str = "uploaded_files"
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".xlsx", ".xls"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "backend/logs/app.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def origins_list(self) -> List[str]:
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

settings = Settings()
