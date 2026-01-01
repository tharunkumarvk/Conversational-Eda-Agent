# backend/db.py
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# Import settings - handle both relative and absolute imports
try:
    from .config import settings
except ImportError:
    from config import settings

# Use DATABASE_URL from settings (supports SQLite or PostgreSQL)
DATABASE_URL = settings.DATABASE_URL

# Configure engine based on database type with better error handling
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # PostgreSQL/MySQL - add connection pooling and timeout settings
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=5,
        max_overflow=10,
        connect_args={
            "connect_timeout": 10,
            "options": "-c timezone=utc"
        }
    )

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
