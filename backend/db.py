# backend/db.py
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.pool import NullPool

# Import settings - handle both relative and absolute imports
try:
    from .config import settings
except ImportError:
    from config import settings

# Use DATABASE_URL from settings (supports SQLite or PostgreSQL)
DATABASE_URL = settings.DATABASE_URL

# Global flag to track database availability
DB_AVAILABLE = False
engine = None
SessionLocal = None

try:
    # Configure engine based on database type with better error handling
    if DATABASE_URL.startswith("sqlite"):
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    else:
        # PostgreSQL with IPv4-only DNS resolution and connection pooling
        # Use sslmode=require for Supabase and prefer IPv4
        if "sslmode" not in DATABASE_URL:
            if "?" in DATABASE_URL:
                DATABASE_URL += "&sslmode=require"
            else:
                DATABASE_URL += "?sslmode=require"
        
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,  # Recycle connections every 5 minutes
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            connect_args={
                "connect_timeout": 10,
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5,
            }
        )
    
    # Don't test connection immediately - let it fail lazily at first use
    # This allows the app to start even if database is unreachable
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    DB_AVAILABLE = True
    print("✅ Database engine created (connection will be tested on first use)")
    
except Exception as e:
    print(f"⚠️ Database connection failed: {e}")
    print("📋 App will start with limited functionality (no database persistence)")
    print(f"📍 Attempted connection to: {DATABASE_URL[:50]}...")
    
    # Fallback to in-memory SQLite for local development
    try:
        print("🔄 Falling back to in-memory SQLite database...")
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        DB_AVAILABLE = True
        print("✅ In-memory database initialized (data won't persist)")
    except Exception as fallback_error:
        print(f"❌ Fallback database also failed: {fallback_error}")
        engine = None
        SessionLocal = None
        DB_AVAILABLE = False

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    google_id = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    picture = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    datasets = relationship("Dataset", back_populates="user", cascade="all, delete-orphan")
    chat_history = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")
    plot_history = relationship("PlotHistory", back_populates="user", cascade="all, delete-orphan")

class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, unique=True, index=True)
    filename = Column(String)
    file_path = Column(String)
    upload_time = Column(DateTime, default=datetime.utcnow)
    rows = Column(Integer, nullable=True)
    columns = Column(Integer, nullable=True)
    size_bytes = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # nullable for migration
    
    # Relationship
    user = relationship("User", back_populates="datasets")

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, index=True)
    user_query = Column(Text)
    ai_response = Column(Text)
    file_id = Column(String, nullable=True)
    ts = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # nullable for migration
    
    # Relationship
    user = relationship("User", back_populates="chat_history")

class PlotHistory(Base):
    __tablename__ = "plot_history"
    id = Column(Integer, primary_key=True, index=True)
    plot_name = Column(String)
    plot_type = Column(String)
    plot_base64 = Column(Text)
    file_id = Column(String, nullable=True)
    ts = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # nullable for migration
    
    # Relationship
    user = relationship("User", back_populates="plot_history")

# Create tables if not exist
def init_db():
    Base.metadata.create_all(bind=engine)

init_db()
