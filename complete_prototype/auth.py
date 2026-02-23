"""
Authentication Module
Handles user login, signup, and session management
"""

import os
import re
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
import bcrypt

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass


# ===== DATABASE CONFIGURATION =====
def get_config(key: str, default: str = "") -> str:
    """Get config from environment or Streamlit secrets"""
    env_value = os.getenv(key)
    if env_value:
        return env_value
    try:
        if hasattr(st, "secrets"):
            secrets_dict = dict(st.secrets)
            if key in secrets_dict:
                return secrets_dict[key]
    except:
        pass
    return default


DATABASE_URL = get_config("DATABASE_URL", "sqlite:///./users.db")

# Create database engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
elif DATABASE_URL.startswith("mysql"):
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


# ===== DATABASE MODELS =====
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    session_token = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)


class UserFile(Base):
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
    __tablename__ = "user_chat_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    message = Column(Text)
    response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    file_context = Column(String(500), nullable=True)


# Initialize database
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Database initialization warning: {e}")


# ===== AUTH FUNCTIONS =====
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except:
        return False


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def create_user(email: str, username: str, password: str, name: str = "") -> Dict[str, Any]:
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter((User.email == email) | (User.username == username)).first()
        if existing_user:
            return {"success": False, "message": "Email or username already exists"}
        
        hashed_pw = hash_password(password)
        new_user = User(email=email, username=username, hashed_password=hashed_pw, name=name or username)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"success": True, "message": "Account created!", "user_id": new_user.id, "username": new_user.username}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error: {str(e)}"}
    finally:
        db.close()


def authenticate_user(username_or_email: str, password: str) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        user = db.query(User).filter((User.username == username_or_email) | (User.email == username_or_email)).first()
        if not user or not user.is_active or not verify_password(password, user.hashed_password):
            return {"success": False, "message": "Invalid credentials"}
        
        user.last_login = datetime.utcnow()
        db.commit()
        
        session_token = generate_session_token()
        session = UserSession(user_id=user.id, session_token=session_token, 
                            expires_at=datetime.utcnow() + timedelta(days=7))
        db.add(session)
        db.commit()
        
        return {"success": True, "message": "Login successful!", "user_id": user.id,
                "username": user.username, "email": user.email, "name": user.name, "session_token": session_token}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error: {str(e)}"}
    finally:
        db.close()


def verify_session(session_token: str) -> Optional[Dict[str, Any]]:
    db = SessionLocal()
    try:
        session = db.query(UserSession).filter(UserSession.session_token == session_token).first()
        if not session or session.expires_at < datetime.utcnow():
            return None
        user = db.query(User).filter(User.id == session.user_id).first()
        if not user or not user.is_active:
            return None
        return {"user_id": user.id, "username": user.username, "email": user.email, "name": user.name}
    except:
        return None
    finally:
        db.close()


def logout_user(session_token: str) -> bool:
    db = SessionLocal()
    try:
        session = db.query(UserSession).filter(UserSession.session_token == session_token).first()
        if session:
            db.delete(session)
            db.commit()
            return True
        return False
    except:
        db.rollback()
        return False
    finally:
        db.close()


def save_user_file(user_id: int, file_id: str, filename: str, file_path: str, file_size: int, rows: int = None, columns: int = None):
    db = SessionLocal()
    try:
        user_file = UserFile(user_id=user_id, file_id=file_id, filename=filename, file_path=file_path,
                           file_size=file_size, rows=rows, columns=columns)
        db.add(user_file)
        db.commit()
        return user_file.id
    except:
        db.rollback()
        return None
    finally:
        db.close()


def save_chat_history(user_id: int, message: str, response: str, file_context: str = None):
    db = SessionLocal()
    try:
        chat = UserChatHistory(user_id=user_id, message=message, response=response, file_context=file_context)
        db.add(chat)
        db.commit()
    except:
        db.rollback()
    finally:
        db.close()


def get_user_chat_history(user_id: int, limit: int = 50):
    db = SessionLocal()
    try:
        chats = db.query(UserChatHistory).filter(UserChatHistory.user_id == user_id)\
                  .order_by(UserChatHistory.timestamp.desc()).limit(limit).all()
        return list(reversed(chats))
    finally:
        db.close()


def get_user_files(user_id: int):
    db = SessionLocal()
    try:
        return db.query(UserFile).filter(UserFile.user_id == user_id).all()
    finally:
        db.close()


# ===== UI FUNCTIONS =====
def is_valid_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_strong_password(password: str) -> tuple:
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Must contain uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Must contain lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Must contain number"
    return True, "Strong password"


def show_login_page():
    """Display login/signup page"""
    st.markdown("""
    <style>
        .auth-header {
            background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 50%, #EC4899 100%);
            padding: 2.5rem;
            border-radius: 12px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 8px 24px rgba(139, 92, 246, 0.4);
        }
        .stButton>button {
            width: 100%;
            background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
            color: white;
            font-weight: 600;
            border-radius: 8px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="auth-header">
        <h1>🤖 DataColombus EDA Agent</h1>
        <p style="margin: 0; opacity: 0.9;">Your AI-Powered Data Analysis Assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            st.subheader("Welcome Back!")
            username_or_email = st.text_input("Username or Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("🚀 Login", use_container_width=True)
            
            if submit:
                if not username_or_email or not password:
                    st.error("Please fill in all fields")
                else:
                    result = authenticate_user(username_or_email, password)
                    if result["success"]:
                        st.session_state.authenticated = True
                        st.session_state.user_id = result["user_id"]
                        st.session_state.username = result["username"]
                        st.session_state.email = result["email"]
                        st.session_state.name = result["name"]
                        st.session_state.session_token = result["session_token"]
                        st.success(f"Welcome back, {result['name']}! 🎉")
                        st.rerun()
                    else:
                        st.error(result["message"])
    
    with tab2:
        with st.form("signup_form"):
            st.subheader("Create Account")
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            st.caption("⚡ Password: 8+ chars, uppercase, lowercase, number")
            
            submit = st.form_submit_button("✨ Create Account", use_container_width=True)
            
            if submit:
                errors = []
                if not all([name, email, username, password, confirm_password]):
                    errors.append("All fields required")
                if not is_valid_email(email):
                    errors.append("Invalid email")
                if len(username) < 3:
                    errors.append("Username too short")
                if password != confirm_password:
                    errors.append("Passwords don't match")
                
                password_valid, password_msg = is_strong_password(password)
                if not password_valid:
                    errors.append(password_msg)
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    result = create_user(email, username, password, name)
                    if result["success"]:
                        st.success(result["message"])
                        st.info("✅ Please login with your new account")
                    else:
                        st.error(result["message"])


def check_authentication():
    """Check if user is authenticated"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if st.session_state.authenticated and "session_token" in st.session_state:
        user_info = verify_session(st.session_state.session_token)
        if user_info:
            return True
        else:
            st.session_state.authenticated = False
            return False
    
    return st.session_state.authenticated


def show_logout_button():
    """Display logout button in sidebar"""
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"**👤 {st.session_state.get('name', 'User')}**")
        st.caption(f"@{st.session_state.get('username', '')}")
        
        if st.button("🚪 Logout", use_container_width=True):
            if "session_token" in st.session_state:
                logout_user(st.session_state.session_token)
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("Logged out!")
            st.rerun()
