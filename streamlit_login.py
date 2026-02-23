"""
Streamlit Login/Signup UI Component
"""

import streamlit as st
import re
from streamlit_auth import authenticate_user, create_user, verify_session, logout_user


def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_strong_password(password: str) -> tuple[bool, str]:
    """Check if password is strong enough"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, "Password is strong"


def show_login_page():
    """Display login/signup page"""
    
    # Custom CSS for auth page - Dark Theme
    st.markdown("""
    <style>
        .auth-container {
            max-width: 500px;
            margin: 0 auto;
            padding: 2rem;
        }
        .auth-header {
            background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 50%, #EC4899 100%);
            padding: 2.5rem;
            border-radius: 12px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 8px 24px rgba(139, 92, 246, 0.4);
        }
        .auth-header h1 {
            margin: 0;
            font-size: 2rem;
            font-weight: 700;
        }
        .auth-tab {
            background: #1E1E2E;
            border: 1px solid #2D2D3D;
            border-radius: 10px;
            padding: 1.5rem;
            margin-top: 1rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }
        .stButton>button {
            width: 100%;
            background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
            color: white;
            font-weight: 600;
            padding: 0.75rem;
            border-radius: 8px;
            border: none;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
            box-shadow: 0 4px 16px rgba(139, 92, 246, 0.5);
            transform: translateY(-2px);
        }
        .stTextInput>div>div>input {
            background: #0E1117;
            border: 1px solid #2D2D3D;
            color: #FAFAFA;
            border-radius: 8px;
        }
        .stTextInput>div>div>input:focus {
            border-color: #8B5CF6;
            box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2);
        }
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            background: #1E1E2E;
            border-radius: 8px;
            color: #FAFAFA;
            border: 1px solid #2D2D3D;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
            border-color: #8B5CF6;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="auth-header">
        <h1>🤖 DataColombus EDA Agent</h1>
        <p style="margin: 0; opacity: 0.9;">Your AI-Powered Data Analysis Assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs for Login/Signup
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
    
    with tab1:
        st.markdown('<div class="auth-tab">', unsafe_allow_html=True)
        with st.form("login_form"):
            st.subheader("Welcome Back!")
            username_or_email = st.text_input("Username or Email", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                submit = st.form_submit_button("🚀 Login", use_container_width=True)
            
            if submit:
                if not username_or_email or not password:
                    st.error("Please fill in all fields")
                else:
                    with st.spinner("Authenticating..."):
                        result = authenticate_user(username_or_email, password)
                    
                    if result["success"]:
                        # Store user info in session
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
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="auth-tab">', unsafe_allow_html=True)
        with st.form("signup_form"):
            st.subheader("Create Your Account")
            
            name = st.text_input("Full Name", key="signup_name")
            email = st.text_input("Email", key="signup_email", autocomplete="email")
            username = st.text_input("Username", key="signup_username")
            password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
            
            # Password requirements hint
            st.caption("⚡ Password must be 8+ characters with uppercase, lowercase, and numbers")
            
            submit = st.form_submit_button("✨ Create Account", use_container_width=True)
            
            if submit:
                # Validation
                errors = []
                
                if not name or not email or not username or not password or not confirm_password:
                    errors.append("All fields are required")
                
                if not is_valid_email(email):
                    errors.append("Invalid email format")
                
                if len(username) < 3:
                    errors.append("Username must be at least 3 characters")
                
                if password != confirm_password:
                    errors.append("Passwords don't match")
                
                password_valid, password_msg = is_strong_password(password)
                if not password_valid:
                    errors.append(password_msg)
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    with st.spinner("Creating your account..."):
                        result = create_user(email, username, password, name)
                    
                    if result["success"]:
                        st.success(result["message"])
                        st.info("✅ Please login with your new account")
                        st.balloons()
                    else:
                        st.error(result["message"])
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; opacity: 0.7; font-size: 0.9em;">
        <p>🔒 Your data is secure and encrypted</p>
        <p>📊 Start analyzing data with AI in seconds</p>
    </div>
    """, unsafe_allow_html=True)


def check_authentication():
    """Check if user is authenticated"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if st.session_state.authenticated:
        # Verify session token if exists
        if "session_token" in st.session_state:
            user_info = verify_session(st.session_state.session_token)
            if user_info:
                return True
            else:
                # Session expired
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
            # Logout from database
            if "session_token" in st.session_state:
                logout_user(st.session_state.session_token)
            
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            st.success("Logged out successfully!")
            st.rerun()
