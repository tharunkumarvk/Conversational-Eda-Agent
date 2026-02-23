"""
Streamlit Authentication Module
Supports email/password authentication with flexible database backend
Works with MySQL, PostgreSQL, or SQLite
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
import bcrypt

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

# Database Configuration - supports both .env and Streamlit secrets
def get_config(key: str, default: str = "") -> str:
    """Get config from Streamlit secrets or environment variables"""
    # Try environment variables first (cleaner, no warnings)
    env_value = os.getenv(key)
    if env_value:
        return env_value
    
    # Try Streamlit secrets only if env var not found (for deployment)
    try:
        if hasattr(st, "secrets"):
            secrets_dict = dict(st.secrets)
            if key in secrets_dict:
                return secrets_dict[key]
    except (KeyError, FileNotFoundError, Exception):
        pass
    
    return default

DATABASE_URL = get_config("DATABASE_URL", "sqlite:///./streamlit_users.db")

# Create engine based on database type
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
elif DATABASE_URL.startswith("mysql"):
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=5,
        max_overflow=10
    )
else:  # PostgreSQL
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=10
    )

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


# Database Models
class User(Base):
    """User model for authentication"""
    __tablename__ = "streamlit_users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # User preferences
    google_id = Column(String(255), unique=True, nullable=True)
    profile_picture = Column(String(500), nullable=True)


class UserSession(Base):
    """User session tracking"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    session_token = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)


class UserFile(Base):
    """Track uploaded files per user"""
    __tablename__ = "user_files"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    file_id = Column(String(255), unique=True, index=True)
    filename = Column(String(255))
    file_path = Column(String(500))
    file_size = Column(Integer)
    upload_time = Column(DateTime, default=datetime.utcnow)
    rows = Column(Integer, nullable=True)
    columns = Column(Integer, nullable=True)


class UserChatHistory(Base):
    """Store chat history per user"""
    __tablename__ = "user_chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    message = Column(Text)
    response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    file_context = Column(String(500), nullable=True)


class UserAnalysis(Base):
    """Store analysis results per user"""
    __tablename__ = "user_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    analysis_type = Column(String(100))
    file_id = Column(String(255))
    analysis_data = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# Initialize database
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
except Exception as e:
    print(f"⚠️ Database initialization warning: {e}")


# Authentication Functions
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except:
        return False


def generate_session_token() -> str:
    """Generate secure session token"""
    return secrets.token_urlsafe(32)


def create_user(email: str, username: str, password: str, name: str = "") -> Dict[str, Any]:
    """Create a new user account"""
    db = SessionLocal()
    try:
        # Check if user exists
        existing_user = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            if existing_user.email == email:
                return {"success": False, "message": "Email already registered"}
            else:
                return {"success": False, "message": "Username already taken"}
        
        # Create new user
        hashed_pw = hash_password(password)
        new_user = User(
            email=email,
            username=username,
            hashed_password=hashed_pw,
            name=name or username
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {
            "success": True,
            "message": "Account created successfully!",
            "user_id": new_user.id,
            "username": new_user.username
        }
    
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error creating account: {str(e)}"}
    finally:
        db.close()


def authenticate_user(username_or_email: str, password: str) -> Dict[str, Any]:
    """Authenticate user with username/email and password"""
    db = SessionLocal()
    try:
        # Find user by username or email
        user = db.query(User).filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        
        if not user:
            return {"success": False, "message": "Invalid credentials"}
        
        if not user.is_active:
            return {"success": False, "message": "Account is inactive"}
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            return {"success": False, "message": "Invalid credentials"}
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Create session token
        session_token = generate_session_token()
        session = UserSession(
            user_id=user.id,
            session_token=session_token,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.add(session)
        db.commit()
        
        return {
            "success": True,
            "message": "Login successful!",
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "name": user.name,
            "session_token": session_token
        }
    
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Login error: {str(e)}"}
    finally:
        db.close()


def verify_session(session_token: str) -> Optional[Dict[str, Any]]:
    """Verify session token and return user info"""
    db = SessionLocal()
    try:
        session = db.query(UserSession).filter(
            UserSession.session_token == session_token
        ).first()
        
        if not session:
            return None
        
        # Check if session expired
        if session.expires_at < datetime.utcnow():
            db.delete(session)
            db.commit()
            return None
        
        # Get user info
        user = db.query(User).filter(User.id == session.user_id).first()
        if not user or not user.is_active:
            return None
        
        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "name": user.name
        }
    
    except Exception as e:
        print(f"Session verification error: {e}")
        return None
    finally:
        db.close()


def logout_user(session_token: str) -> bool:
    """Logout user by invalidating session"""
    db = SessionLocal()
    try:
        session = db.query(UserSession).filter(
            UserSession.session_token == session_token
        ).first()
        
        if session:
            db.delete(session)
            db.commit()
            return True
        return False
    
    except Exception as e:
        db.rollback()
        print(f"Logout error: {e}")
        return False
    finally:
        db.close()


def get_user_files(user_id: int):
    """Get all files for a user"""
    db = SessionLocal()
    try:
        files = db.query(UserFile).filter(UserFile.user_id == user_id).all()
        return files
    finally:
        db.close()


def save_user_file(user_id: int, file_id: str, filename: str, file_path: str, 
                   file_size: int, rows: int = None, columns: int = None):
    """Save file metadata for user"""
    db = SessionLocal()
    try:
        user_file = UserFile(
            user_id=user_id,
            file_id=file_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            rows=rows,
            columns=columns
        )
        db.add(user_file)
        db.commit()
        return user_file.id
    except Exception as e:
        db.rollback()
        print(f"Error saving file metadata: {e}")
        return None
    finally:
        db.close()


def save_chat_history(user_id: int, message: str, response: str, file_context: str = None):
    """Save chat history for user"""
    db = SessionLocal()
    try:
        chat = UserChatHistory(
            user_id=user_id,
            message=message,
            response=response,
            file_context=file_context
        )
        db.add(chat)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error saving chat: {e}")
    finally:
        db.close()


def get_user_chat_history(user_id: int, limit: int = 50):
    """Get chat history for user"""
    db = SessionLocal()
    try:
        chats = db.query(UserChatHistory).filter(
            UserChatHistory.user_id == user_id
        ).order_by(UserChatHistory.timestamp.desc()).limit(limit).all()
        return list(reversed(chats))
    finally:
        db.close()
