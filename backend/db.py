# backend/db.py
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "eda_agent.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, unique=True, index=True)
    filename = Column(String)
    file_path = Column(String)
    upload_time = Column(DateTime, default=datetime.utcnow)

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, index=True)
    user_query = Column(Text)
    ai_response = Column(Text)
    ts = Column(DateTime, default=datetime.utcnow)

class PlotHistory(Base):
    __tablename__ = "plot_history"
    id = Column(Integer, primary_key=True, index=True)
    plot_name = Column(String)
    plot_type = Column(String)
    plot_base64 = Column(Text)
    ts = Column(DateTime, default=datetime.utcnow)

# Create tables if not exist
def init_db():
    Base.metadata.create_all(bind=engine)

init_db()
