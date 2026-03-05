# Complete Agentic EDA Agent with LangGraph - AUTONOMOUS VERSION
# Streamlit App with UI Tools + Conversational AI

import sys
if sys.platform.startswith("win"):
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Core imports
import os
import io
import time
import json
import tempfile
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict

# Data science imports
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Plotly imports
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.express import scatter_3d, line_3d, bar_polar, density_contour, sunburst, treemap, funnel, choropleth

# ML imports
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import KNNImputer, IterativeImputer, SimpleImputer
from sklearn.preprocessing import (StandardScaler, MinMaxScaler, RobustScaler, PowerTransformer, 
                                  OrdinalEncoder, OneHotEncoder, LabelBinarizer, LabelEncoder)
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.feature_selection import VarianceThreshold, SelectKBest, chi2
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.manifold import TSNE
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler

# Fuzzy matching
from fuzzywuzzy import process
import recordlinkage

# LangGraph imports
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

# Gemini imports
import google.generativeai as genai

# Gemini
import google.generativeai as genai

# LangGraph imports with error handling
try:
    from langgraph.graph import StateGraph, END
    from langchain_core.messages import HumanMessage, AIMessage
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.tools import tool
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("LangGraph not available - using fallback mode")

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except:
    pass

# ===== AWS Integration =====
AWS_AVAILABLE = False
try:
    from aws.config import aws_config
    from aws.dynamodb import dynamo_db
    from aws.cognito import cognito_auth
    from aws.cloudwatch_logger import cw_logger
    from aws.ssm import ssm_config
    from aws.sqs_client import sqs_client
    from aws.lambda_client import lambda_client
    from aws.s3_storage import s3_storage
    AWS_AVAILABLE = aws_config.aws_enabled
    if AWS_AVAILABLE:
        print(f"✅ AWS services loaded (region: {aws_config.region})")
        cw_logger.info("EDA Agent started", services=str(aws_config.get_status()))
except ImportError as e:
    print(f"⚠️ AWS module not available: {e}")
    aws_config = None
    dynamo_db = None
    cognito_auth = None
    cw_logger = None
    ssm_config = None
    sqs_client = None
    lambda_client = None
    s3_storage = None
except Exception as e:
    print(f"⚠️ AWS initialization error: {e}")
    aws_config = None
    dynamo_db = None
    cognito_auth = None
    cw_logger = None
    ssm_config = None
    sqs_client = None
    lambda_client = None
    s3_storage = None

# Page config
st.set_page_config(
    page_title="🤖 Agentic EDA Agent", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== AUTHENTICATION =====
# Auth mode: 'cognito' (AWS), 'local' (SQLAlchemy/bcrypt), or False (disabled)
AUTH_MODE = os.getenv("AUTH_MODE", "false").lower()
AUTH_ENABLED = AUTH_MODE in ("cognito", "local", "true")
USE_COGNITO = AUTH_MODE == "cognito" and AWS_AVAILABLE and cognito_auth and cognito_auth.available

if AUTH_ENABLED and USE_COGNITO:
    # === AWS Cognito Authentication ===
    if "cognito_authenticated" not in st.session_state:
        st.session_state.cognito_authenticated = False
        st.session_state.cognito_tokens = {}
        st.session_state.cognito_user = {}
    
    if not st.session_state.cognito_authenticated:
        st.markdown("""<div style='max-width:500px;margin:0 auto;text-align:center;padding:2rem;'>
        <h1>🔐 EDA Agent Login</h1></div>""", unsafe_allow_html=True)
        
        auth_tab1, auth_tab2 = st.tabs(["Login", "Sign Up"])
        with auth_tab1:
            email = st.text_input("Email", key="cognito_login_email")
            password = st.text_input("Password", type="password", key="cognito_login_pw")
            if st.button("Sign In", type="primary", use_container_width=True):
                result = cognito_auth.sign_in(email, password)
                if result["success"]:
                    st.session_state.cognito_authenticated = True
                    st.session_state.cognito_tokens = {
                        "access_token": result["access_token"],
                        "id_token": result["id_token"],
                        "refresh_token": result["refresh_token"],
                    }
                    st.session_state.cognito_user = result.get("user_info", {})
                    st.session_state.user_id = result["user_info"].get("sub", "")
                    if cw_logger:
                        cw_logger.info(f"User signed in: {email}")
                    st.rerun()
                else:
                    st.error(result["message"])
        
        with auth_tab2:
            new_email = st.text_input("Email", key="cognito_signup_email")
            new_name = st.text_input("Name", key="cognito_signup_name")
            new_password = st.text_input("Password", type="password", key="cognito_signup_pw")
            confirm_pw = st.text_input("Confirm Password", type="password", key="cognito_signup_pw2")
            if st.button("Create Account", use_container_width=True):
                if new_password != confirm_pw:
                    st.error("Passwords don't match")
                else:
                    result = cognito_auth.sign_up(new_email, new_password, new_name)
                    if result["success"]:
                        st.success(result["message"])
                        st.info("Enter the verification code sent to your email:")
                        st.session_state._cognito_pending_email = new_email
                    else:
                        st.error(result["message"])
            
            # Verification code input
            if st.session_state.get("_cognito_pending_email"):
                code = st.text_input("Verification Code", key="cognito_verify_code")
                if st.button("Verify Email"):
                    result = cognito_auth.confirm_sign_up(
                        st.session_state._cognito_pending_email, code)
                    if result["success"]:
                        st.success("Email verified! You can now sign in.")
                        del st.session_state._cognito_pending_email
                    else:
                        st.error(result["message"])
        
        st.stop()
    
    # Logout button
    if st.sidebar.button("🚪 Logout"):
        if st.session_state.cognito_tokens.get("access_token"):
            cognito_auth.sign_out(st.session_state.cognito_tokens["access_token"])
        st.session_state.cognito_authenticated = False
        st.session_state.cognito_tokens = {}
        st.session_state.cognito_user = {}
        st.rerun()
    
    user_display = st.session_state.cognito_user.get("name") or st.session_state.cognito_user.get("email", "User")
    st.sidebar.markdown(f"👤 **{user_display}**")
    st.sidebar.markdown("---")

elif AUTH_ENABLED and not USE_COGNITO:
    # === Local bcrypt + DynamoDB/SQLAlchemy Authentication ===
    from streamlit_login import check_authentication, show_login_page, show_logout_button
    from streamlit_auth import save_user_file, save_chat_history, get_user_chat_history

    if not check_authentication():
        show_login_page()
        st.stop()

    show_logout_button()

    # Navigation
    st.sidebar.markdown("---")
    st.sidebar.title("🧭 Navigation")

    if "current_page" not in st.session_state:
        st.session_state.current_page = "main"

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🏠 Main App", use_container_width=True, type="primary" if st.session_state.current_page == "main" else "secondary"):
            st.session_state.current_page = "main"
            st.rerun()
    with col2:
        if st.button("📚 History", use_container_width=True, type="primary" if st.session_state.current_page == "history" else "secondary"):
            st.session_state.current_page = "history"
            st.rerun()

    st.sidebar.markdown("---")

    if st.session_state.current_page == "history":
        from streamlit_history import show_user_history
        show_user_history()
        st.stop()

# Session-based context (always active — works without DB)
if "session_chat_log" not in st.session_state:
    st.session_state.session_chat_log = []
if "session_file_log" not in st.session_state:
    st.session_state.session_file_log = []

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 50%, #EC4899 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
    }
    .tool-card {
        background: #1E1E2E;
        border: 1px solid #2D2D3D;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }
    .success-box {
        background: #1E3A2E;
        border: 1px solid #2D5A3E;
        color: #4ADE80;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .error-box {
        background: #3A1E1E;
        border: 1px solid #5A2D2D;
        color: #F87171;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    /* Dark theme enhancements */
    .stExpander {
        background: #1E1E2E;
        border: 1px solid #2D2D3D;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background: #1E1E2E;
        border-radius: 8px;
        color: #FAFAFA;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
    }
    div[data-testid="stMetricValue"] {
        color: #8B5CF6;
    }
</style>
""", unsafe_allow_html=True)

# --- Data Classes for State Management ---
@dataclass  
class FileMetadata:
    name: str
    shape: Tuple[int, int]
    columns: List[str]
    dtypes: Dict[str, str]
    missing_count: Dict[str, int]
    uploaded_at: str
    file_size: int

@dataclass
class ProcessingHistory:
    action: str
    params: Dict[str, Any]
    timestamp: str
    result_shape: Tuple[int, int]
    success: bool
    message: str

# --- Gemini Configuration ---
def init_genai():
    """Initialize Google Generative AI with proper error handling"""
    # Try environment variables first (cleaner, no warnings)
    key = os.getenv("GOOGLE_API_KEY")
    
    # Try Streamlit secrets only if env var not found (for deployment)
    if not key:
        try:
            if hasattr(st, "secrets"):
                secrets_dict = dict(st.secrets)
                key = secrets_dict.get("GOOGLE_API_KEY")
        except (FileNotFoundError, KeyError, Exception):
            pass
    
    if not key:
        st.error("GOOGLE_API_KEY not found in environment variables or Streamlit secrets!")
        return None
    try:
        genai.configure(api_key=key)
        # Test the connection
        models = list(genai.list_models())
        return genai
    except Exception as e:
        st.error(f"Gemini initialization error: {e}")
        return None

def ask_gemini_basic(prompt: str, context: Dict[str, Any] = None) -> str:
    """Basic Gemini API call with error handling"""
    if not GENAI:
        return "❌ Gemini not available - please check your API key"
    
    try:
        # Use the correct model name
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Add context about files if available
        context_str = ""
        if context and "files" in context:
            context_str = "\nAvailable files:\n"
            for idx, file_data in context["files"].items():
                metadata = file_data["metadata"]
                context_str += f"File {idx}: {metadata.name} ({metadata.shape[0]}x{metadata.shape[1]})\n"
        
        full_prompt = f"""You are an EDA (Exploratory Data Analysis) agent. Help users analyze their datasets.

{context_str}

User request: {prompt}

Provide a helpful response about what analysis or operations should be performed. Be specific and actionable."""
        
        # ✅ Correct way to call Gemini
        response = model.generate_content(
            contents=[{
                "role": "user",
                "parts": [{"text": full_prompt}]
            }]
        )
        
        # ✅ Safely extract text
        return response.candidates[0].content.parts[0].text if response.candidates else "No response generated"
    
    except Exception as e:
        return f"❌ Error calling Gemini: {str(e)}"

GENAI = init_genai()

# --- Session State Initialization ---
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'files': {},  # idx -> {"df": DataFrame, "metadata": FileMetadata}
        'last_idx': None,
        'preprocessed_files': {},  # name -> DataFrame
        'processing_history': [],  # List[ProcessingHistory]
        'chat_history': [],  # List[Dict]
        'agent_state': {},
        'current_analysis': None,
        'plot_cache': {},
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

init_session_state()

# --- File Operations ---
def load_file_buffer(uploaded_file):
    """Load CSV/Excel file into DataFrame with robust error handling"""
    try:
        if uploaded_file.name.lower().endswith('.csv'):
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            for encoding in encodings:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding=encoding)
                    return df
                except UnicodeDecodeError:
                    continue
            # If all encodings fail, try with error handling
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding='utf-8', errors='replace')
            return df
        elif uploaded_file.name.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
            return df
        else:
            raise ValueError(f"Unsupported file format: {uploaded_file.name}")
        
    except Exception as e:
        st.error(f"Failed to load {uploaded_file.name}: {str(e)}")
        return None

def add_file(df: pd.DataFrame, name: str) -> int:
    """Add file to session state and return index"""
    idx = max(st.session_state.files.keys(), default=-1) + 1
    
    # Create metadata with safe type conversion
    metadata = FileMetadata(
        name=name,
        shape=df.shape,
        columns=df.columns.tolist(),
        dtypes={col: str(dtype) for col, dtype in df.dtypes.items()},
        missing_count=df.isnull().sum().to_dict(),
        uploaded_at=datetime.now().isoformat(),
        file_size=int(df.memory_usage(deep=True).sum())
    )
    
    st.session_state.files[idx] = {
        "df": df.copy(),
        "metadata": metadata
    }
    st.session_state.last_idx = idx
    
    # Track file in session + database (if auth enabled)
    try:
        st.session_state.session_file_log.append({
            "filename": name,
            "rows": df.shape[0],
            "columns": df.shape[1],
            "file_size": metadata.file_size,
            "timestamp": datetime.now().isoformat()
        })
        if AUTH_ENABLED:
            import uuid
            file_id = str(uuid.uuid4())
            save_user_file(
                user_id=st.session_state.user_id,
                file_id=file_id,
                filename=name,
                file_path=f"session_{st.session_state.user_id}/{file_id}",
                file_size=metadata.file_size,
                rows=df.shape[0],
                columns=df.shape[1]
            )
    except Exception:
        pass
    
    return idx

def get_file_by_ref(ref) -> Tuple[Optional[pd.DataFrame], Optional[str], Optional[int]]:
    """Get file by reference (index or name)"""
    if ref is None or ref == "":
        idx = st.session_state.last_idx
        if idx is None or idx not in st.session_state.files:
            return None, None, None
        file_data = st.session_state.files[idx]
        return file_data["df"].copy(), file_data["metadata"].name, idx
    
    # Try integer index
    try:
        idx = int(ref)
        if idx in st.session_state.files:
            file_data = st.session_state.files[idx]
            return file_data["df"].copy(), file_data["metadata"].name, idx
    except (ValueError, TypeError):
        pass
    
    # Try name matching
    ref_lower = str(ref).lower()
    for idx, file_data in st.session_state.files.items():
        if ref_lower in file_data["metadata"].name.lower():
            return file_data["df"].copy(), file_data["metadata"].name, idx
    
    # Fallback to last file
    return get_file_by_ref(None)

def merge_dataframes(left_df: pd.DataFrame, right_df: pd.DataFrame, 
                     left_on: Union[str, List[str]] = None, right_on: Union[str, List[str]] = None, 
                     how: str = "inner", concat_axis: int = None,
                     suffixes: List[str] = ["_left", "_right"],
                     indicator: bool = False,
                     validate: str = None,  # one_to_one, one_to_many, etc.
                     fuzzy: bool = False, fuzzy_threshold: int = 80) -> Tuple[pd.DataFrame, str]:
    """Comprehensive merging with all pandas options and advanced"""
    try:
        if concat_axis is not None:
            merged = pd.concat([left_df, right_df], axis=concat_axis, ignore_index=True, join='outer', keys=None, sort=False)
            return merged, f"Concatenated along axis {concat_axis}"
        
        if fuzzy:
            if left_df.shape[0] * right_df.shape[0] > 1_000_000:  # Prevent OOM for large datasets
                return None, "Fuzzy matching skipped: Datasets too large for full comparison. Use blocking or smaller data."
    
        if isinstance(left_on, str) and isinstance(right_on, str):
            choices = {idx: str(val) for idx, val in right_df[right_on].items()}  # Convert to str for safety
            matches = [process.extractOne(str(val), choices) for val in left_df[left_on]]  # str for safety
            match_results = [(i, m[2], m[1]) for i, m in enumerate(matches) if m[1] >= fuzzy_threshold]
            if not match_results:
                return None, "No fuzzy matches found"
            left_indices = [mr[0] for mr in match_results]
            right_indices = [mr[1] for mr in match_results]
            left_matched = left_df.iloc[left_indices].reset_index(drop=True)
            right_matched = right_df.iloc[right_indices].reset_index(drop=True)
            merged = left_matched.join(right_matched, lsuffix=suffixes[0], rsuffix=suffixes[1])
            return merged, f"Fuzzy merged {len(match_results)} rows with threshold {fuzzy_threshold}"
        else:
        # Multi-column fuzzy
            indexer = recordlinkage.Index()
            indexer.full()  # Warning: slow for large data
            candidates = indexer.index(left_df, right_df)
            compare = recordlinkage.Compare()
            left_on_list = left_on if isinstance(left_on, list) else [left_on]
            right_on_list = right_on if isinstance(right_on, list) else [right_on]
            for l, r in zip(left_on_list, right_on_list):
                compare.string(l, r, method='levenshtein', threshold=0.85, label=r)  # Fuzzy string compare
            features = compare.compute(candidates, left_df, right_df)
            num_compares = len(left_on_list)
            matches = features[features.sum(axis=1) >= num_compares * 0.85]
            if matches.empty:
                return None, "No fuzzy matches found"
            left_indices = matches.index.get_level_values(0)
            right_indices = matches.index.get_level_values(1)
            left_matched = left_df.loc[left_indices].reset_index(drop=True)
            right_matched = right_df.loc[right_indices].reset_index(drop=True)
            merged = left_matched.join(right_matched, lsuffix=suffixes[0], rsuffix=suffixes[1])
            return merged, f"Fuzzy merged {len(matches)} rows using record linkage"
        
        # Standard merge with all options
        if left_on and right_on:
            # Explicit join keys
            if all(c in left_df.columns for c in (left_on if isinstance(left_on, list) else [left_on])) and all(c in right_df.columns for c in (right_on if isinstance(right_on, list) else [right_on])):
                merged = pd.merge(left_df, right_df, left_on=left_on, right_on=right_on, how=how, suffixes=suffixes, indicator=indicator, validate=validate)
                return merged, f"Merged on {left_on} ↔ {right_on} with how={how}"
            else:
                return None, f"Columns not found"
        
        # Auto-detect common columns
        common_cols = list(set(left_df.columns) & set(right_df.columns))
        if common_cols:
            merged = pd.merge(left_df, right_df, on=common_cols, how=how, suffixes=suffixes, indicator=indicator, validate=validate)
            return merged, f"Merged on common columns: {common_cols}"
        
        # Index-based merge as fallback
        merged = pd.merge(left_df.reset_index(drop=True), right_df.reset_index(drop=True), 
                         left_index=True, right_index=True, how=how, suffixes=suffixes, indicator=indicator, validate=validate)
        return merged, "Index-based merge"
        
    except Exception as e:
        return None, f"Merge failed: {str(e)}"

# --- Data Analysis Tools ---
def generate_data_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate comprehensive data profile with error handling"""
    try:
        profile = {
            "shape": df.shape,
            "memory_usage": int(df.memory_usage(deep=True).sum()),
            "dtypes": df.dtypes.apply(str).to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "missing_percentage": (df.isnull().sum() / len(df) * 100).to_dict(),
            "duplicate_rows": int(df.duplicated().sum()),
            "numeric_summary": {},
            "categorical_summary": {},
            "data_quality_score": 0.0
        }
        
        # Numeric columns analysis
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            profile["numeric_summary"] = df[numeric_cols].describe().to_dict()
            
            # Detect outliers using IQR method
            outliers = {}
            for col in numeric_cols:
                try:
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    if IQR > 0:
                        lower_bound = Q1 - 1.5 * IQR
                        upper_bound = Q3 + 1.5 * IQR
                        outliers[col] = int(((df[col] < lower_bound) | (df[col] > upper_bound)).sum())
                    else:
                        outliers[col] = 0
                except:
                    outliers[col] = 0
            profile["outliers"] = outliers
        
        # Categorical columns analysis
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(categorical_cols) > 0:
            cat_summary = {}
            for col in categorical_cols:
                try:
                    unique_count = df[col].nunique()
                    mode_val = df[col].mode().iloc[0] if not df[col].mode().empty else "N/A"
                    cat_summary[col] = {
                        "unique_count": int(unique_count),
                        "most_frequent": str(mode_val),
                        "frequency": df[col].value_counts().head().to_dict()
                    }
                except:
                    cat_summary[col] = {"unique_count": 0, "most_frequent": "N/A", "frequency": {}}
            profile["categorical_summary"] = cat_summary
        
        # Calculate data quality score (0-100)
        try:
            quality_factors = []
            # Completeness (30%)
            completeness = (1 - df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 30
            quality_factors.append(max(0, completeness))
            
            # Uniqueness (20%)
            uniqueness = (1 - profile["duplicate_rows"] / df.shape[0]) * 20 if df.shape[0] > 0 else 0
            quality_factors.append(max(0, uniqueness))
            
            # Volume adequacy (25%)
            volume = min(len(df) / 1000, 1) * 25
            quality_factors.append(volume)
            
            # Feature richness (25%)
            feature_richness = min(len(df.columns) / 10, 1) * 25
            quality_factors.append(feature_richness)
            
            profile["data_quality_score"] = sum(quality_factors)
        except:
            profile["data_quality_score"] = 50.0  # Default score
        
        return profile
    except Exception as e:
        st.error(f"Error generating data profile: {e}")
        return {
            "shape": df.shape,
            "memory_usage": 0,
            "dtypes": {},
            "missing_values": {},
            "missing_percentage": {},
            "duplicate_rows": 0,
            "numeric_summary": {},
            "categorical_summary": {},
            "data_quality_score": 0.0
        }
    
# 1. Add the missing create_smart_visualizations function after generate_data_profile (around line 300-350, before enhanced_preprocessing)
def create_smart_visualizations(df: pd.DataFrame, max_plots: int = 12) -> List[Tuple[str, any]]:
    """Generate intelligent visualizations based on data characteristics"""
    plots = []
    
    try:
        # Sample data if too large
        sample_df = df.sample(min(2000, len(df))) if len(df) > 2000 else df
        
        numeric_cols = sample_df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = sample_df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # 1. Correlation heatmap for numeric data
        if len(numeric_cols) >= 2:
            try:
                corr_matrix = sample_df[numeric_cols].corr()
                fig = px.imshow(corr_matrix.round(2), 
                               text_auto=True, 
                               color_continuous_scale='RdBu',
                               title="📊 Feature Correlation Matrix")
                plots.append(("Correlation Heatmap", fig))
            except Exception as e:
                st.warning(f"Could not create correlation plot: {e}")
        
        # 2. Distribution plots for numeric columns (limit to first 3)
        for col in numeric_cols[:3]:
            try:
                fig = make_subplots(rows=1, cols=2, 
                                   subplot_titles=[f"Distribution - {col}", f"Box Plot - {col}"])
                
                # Histogram
                fig.add_trace(go.Histogram(x=sample_df[col], name="Distribution", nbinsx=30), row=1, col=1)
                
                # Box plot
                fig.add_trace(go.Box(y=sample_df[col], name="Box Plot"), row=1, col=2)
                
                fig.update_layout(title_text=f"📈 Distribution Analysis: {col}", showlegend=False)
                plots.append((f"Distribution - {col}", fig))
            except Exception as e:
                st.warning(f"Could not create distribution plot for {col}: {e}")
        
        # 3. Category analysis for categorical columns (limit to first 2)
        for col in categorical_cols[:2]:
            try:
                if sample_df[col].nunique() <= 20:  # Only for reasonable number of categories
                    value_counts = sample_df[col].value_counts().head(10)
                    if len(value_counts) > 0:
                        fig = px.bar(x=value_counts.index, y=value_counts.values,
                                    title=f"📊 Top Categories: {col}",
                                    labels={'x': col, 'y': 'Count'})
                        fig.update_layout(xaxis_tickangle=-45)
                        plots.append((f"Categories - {col}", fig))
            except Exception as e:
                st.warning(f"Could not create category plot for {col}: {e}")
        
        # 4. Scatter plots for numeric pairs (max 2)
        if len(numeric_cols) >= 2:
            for i in range(min(2, len(numeric_cols)-1)):
                try:
                    x_col, y_col = numeric_cols[i], numeric_cols[i+1]
                    fig = px.scatter(sample_df, x=x_col, y=y_col,
                                   title=f"🔗 Relationship: {x_col} vs {y_col}")
                    plots.append((f"Scatter - {x_col} vs {y_col}", fig))
                except Exception as e:
                    st.warning(f"Could not create scatter plot: {e}")
        
        # 5. Additional plots with better error handling
        try:
            if len(numeric_cols) >= 2:
                # Create a proper pairplot using matplotlib
                plt.figure(figsize=(10, 8))
                pair_cols = numeric_cols[:4]  # Limit to 4 to avoid performance issues
                pair_df = sample_df[pair_cols].dropna()
                if len(pair_df) > 0:
                    sns.pairplot(pair_df)
                    plt.tight_layout()
                    plots.append(("Pairplot", plt.gcf()))
                    plt.close()
        except Exception as e:
            st.warning(f"Could not create pairplot: {e}")
            
        try:
            if len(categorical_cols) > 0 and len(numeric_cols) > 0:
                fig, ax = plt.subplots(figsize=(10, 6))
                clean_df = sample_df[[categorical_cols[0], numeric_cols[0]]].dropna()
                if len(clean_df) > 0 and clean_df[categorical_cols[0]].nunique() <= 10:
                    sns.boxplot(data=clean_df, x=categorical_cols[0], y=numeric_cols[0], ax=ax)
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    plots.append((f"Box Plot - {categorical_cols[0]} vs {numeric_cols[0]}", fig))
                plt.close()
        except Exception as e:
            st.warning(f"Could not create boxplot: {e}")
            
        try:
            if len(numeric_cols) >= 3:
                fig = px.scatter_3d(sample_df, x=numeric_cols[0], y=numeric_cols[1], z=numeric_cols[2],
                                   title=f"3D Scatter: {numeric_cols[0]} vs {numeric_cols[1]} vs {numeric_cols[2]}")
                plots.append(("3D Scatter", fig))
        except Exception as e:
            st.warning(f"Could not create 3D scatter: {e}")
            
        try:
            if len(numeric_cols) > 0:
                fig, ax = plt.subplots(figsize=(8, 6))
                clean_series = sample_df[numeric_cols[0]].dropna()
                if len(clean_series) > 0:
                    sns.kdeplot(clean_series, fill=True, ax=ax)
                    ax.set_title(f"KDE Plot - {numeric_cols[0]}")
                    plt.tight_layout()
                    plots.append((f"KDE - {numeric_cols[0]}", fig))
                plt.close()
        except Exception as e:
            st.warning(f"Could not create KDE plot: {e}")
        
        return plots[:max_plots]
    
    except Exception as e:
        st.error(f"Visualization creation failed: {e}")
        return []

# --- ENHANCED Preprocessing Functions ---
def enhanced_preprocessing(df: pd.DataFrame, params: Dict[str, Any]) -> Tuple[pd.DataFrame, List[str]]:
    """Comprehensive preprocessing with all common techniques"""
    df_processed = df.copy()
    actions = []
    
    try:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()
        
        # 1. Handle missing values - expanded strategies
        if params.get('handle_missing', True):
            missing_strategy = params.get('missing_strategy', 'mean')  # mean, median, mode, knn, iterative, drop
            if missing_strategy in ['mean', 'median', 'mode']:
                imputer = SimpleImputer(strategy=missing_strategy)
                for col in numeric_cols:
                    if df[col].isnull().sum() > 0:
                        df_processed[col] = imputer.fit_transform(df_processed[[col]])
                        actions.append(f"Filled {col} missing with {missing_strategy}")
            elif missing_strategy == 'knn':
                imputer = KNNImputer(n_neighbors=params.get('knn_neighbors', 5))
                df_processed[numeric_cols] = imputer.fit_transform(df_processed[numeric_cols])
                actions.append(f"Applied KNN imputation to numeric columns")
            elif missing_strategy == 'iterative':
                imputer = IterativeImputer(max_iter=params.get('iter_max', 10))
                df_processed[numeric_cols] = imputer.fit_transform(df_processed[numeric_cols])
                actions.append(f"Applied Iterative imputation to numeric columns")
            elif missing_strategy == 'drop':
                df_processed = df_processed.dropna()
                actions.append("Dropped rows with missing values")
            
            # Categorical missing
            cat_strategy = params.get('cat_missing_strategy', 'mode')  # mode, constant
            if cat_strategy == 'mode':
                for col in categorical_cols:
                    if df[col].isnull().sum() > 0:
                        mode_val = df[col].mode().iloc[0] if not df[col].mode().empty else 'Unknown'
                        df_processed[col] = df_processed[col].fillna(mode_val)
                        actions.append(f"Filled {col} missing with mode ({mode_val})")
            elif cat_strategy == 'constant':
                fill_val = params.get('constant_value', 'Unknown')
                df_processed[categorical_cols] = df_processed[categorical_cols].fillna(fill_val)
                actions.append(f"Filled categorical missing with constant '{fill_val}'")
        
        # 2. Outlier handling - expanded
        if params.get('handle_outliers', False):
            outlier_method = params.get('outlier_method', 'iqr')  # iqr, zscore, isolation_forest
            outlier_action = params.get('outlier_action', 'cap')  # cap, remove, transform (e.g., log)
            
            for col in numeric_cols:
                try:
                    if outlier_method == 'iqr':
                        # ... (keep existing)
                        Q1 = df_processed[col].quantile(0.25)
                        Q3 = df_processed[col].quantile(0.75)
                        IQR = Q3 - Q1
                        if IQR > 0:
                            lower_bound = Q1 - 1.5 * IQR
                            upper_bound = Q3 + 1.5 * IQR
                            outlier_mask = (df_processed[col] < lower_bound) | (df_processed[col] > upper_bound)
                            outlier_count = outlier_mask.sum()
                            
                            if outlier_count > 0:
                                if outlier_action == 'cap':
                                    df_processed[col] = df_processed[col].astype(float)
                                    df_processed.loc[df_processed[col] < lower_bound, col] = lower_bound
                                    df_processed.loc[df_processed[col] > upper_bound, col] = upper_bound
                                    actions.append(f"Capped {outlier_count} outliers in {col} using IQR method")
                                elif outlier_action == 'remove':
                                    df_processed = df_processed[~outlier_mask]
                                    actions.append(f"Removed {outlier_count} outlier rows based on {col}")

                    elif outlier_method == 'zscore':
                        # ... (keep existing)
                        from scipy import stats
                        z_scores = np.abs(stats.zscore(df_processed[col]))
                        outlier_mask = z_scores > 3
                        outlier_count = outlier_mask.sum()
                        
                        if outlier_count > 0 and outlier_action == 'cap':
                            # Cap at 3 standard deviations
                            mean_val = df_processed[col].mean()
                            std_val = df_processed[col].std()
                            lower_bound = mean_val - 3 * std_val
                            upper_bound = mean_val + 3 * std_val
                            df_processed.loc[df_processed[col] < lower_bound, col] = lower_bound
                            df_processed.loc[df_processed[col] > upper_bound, col] = upper_bound
                            actions.append(f"Capped {outlier_count} outliers in {col} using Z-score method")

                    elif outlier_method == 'isolation_forest':
                        iso = IsolationForest(contamination=params.get('contamination', 0.05))
                        outliers = iso.fit_predict(df_processed[[col]])
                        outlier_mask = outliers == -1
                        outlier_count = outlier_mask.sum()
                        if outlier_count > 0:
                            if outlier_action == 'remove':
                                df_processed = df_processed[~outlier_mask]
                            elif outlier_action == 'cap':
                                # Use quantiles for capping
                                lower, upper = df_processed[col].quantile([0.01, 0.99])
                                df_processed[col] = np.clip(df_processed[col], lower, upper)
                            actions.append(f"Handled {outlier_count} outliers in {col} using Isolation Forest")
                    
                    if outlier_action == 'transform':
                        transformer = PowerTransformer(method=params.get('transform_method', 'yeo-johnson'))
                        df_processed[col] = transformer.fit_transform(df_processed[[col]])
                        actions.append(f"Applied power transform to {col} for outliers")
                
                except Exception as e:
                    actions.append(f"Outlier handling failed for {col}: {str(e)}")
        
        # 3. Scaling/Normalization - expanded
        scale_type = params.get('scale_type', None)  # minmax, standard, robust, none
        if scale_type == 'minmax':
            scaler = MinMaxScaler()
            df_processed[numeric_cols] = scaler.fit_transform(df_processed[numeric_cols])
            actions.append("Applied Min-Max scaling")
        elif scale_type == 'standard':
            scaler = StandardScaler()
            df_processed[numeric_cols] = scaler.fit_transform(df_processed[numeric_cols])
            actions.append("Applied Standard scaling")
        elif scale_type == 'robust':
            scaler = RobustScaler()
            df_processed[numeric_cols] = scaler.fit_transform(df_processed[numeric_cols])
            actions.append("Applied Robust scaling")
        
        # 4. Encoding - expanded
        if params.get('encode_categoricals', False):
            encode_method = params.get('encode_method', 'onehot')  # onehot, label, ordinal, binary, frequency, target
            max_cat = params.get('max_categories', 10)
            for col in categorical_cols:
                unique_count = df_processed[col].nunique()
                if unique_count <= max_cat:
                    if encode_method == 'onehot':
                        dummies = pd.get_dummies(df_processed[col], prefix=col, drop_first=True)
                        df_processed = pd.concat([df_processed.drop(col, axis=1), dummies], axis=1)
                        actions.append(f"One-hot encoded {col}")
                    elif encode_method == 'ordinal':
                        oe = OrdinalEncoder()
                        df_processed[col] = oe.fit_transform(df_processed[[col]])
                        actions.append(f"Ordinal encoded {col}")
                    elif encode_method == 'binary':
                        lb = LabelBinarizer()
                        df_processed[col] = lb.fit_transform(df_processed[col])
                        actions.append(f"Binary encoded {col}")
                else:
                    if encode_method == 'label':
                        le = LabelEncoder()
                        df_processed[col] = le.fit_transform(df_processed[col].astype(str))
                        actions.append(f"Label encoded {col}")
                    elif encode_method == 'frequency':
                        freq = df_processed[col].value_counts(normalize=True)
                        df_processed[col] = df_processed[col].map(freq)
                        actions.append(f"Frequency encoded {col}")
                    # Target encoding requires target; assume if provided
                    if encode_method == 'target' and 'target_col' in params:
                        mean = df_processed.groupby(col)[params['target_col']].mean()
                        df_processed[col] = df_processed[col].map(mean)
                        actions.append(f"Target encoded {col}")
        
        # 5. Dimensionality Reduction
        if params.get('reduce_dimensions', False):
            red_method = params.get('red_method', 'pca')  # pca, tsne, svd, lda
            n_components = params.get('n_components', 2)
            if red_method == 'pca':
                pca = PCA(n_components=n_components)
                reduced = pca.fit_transform(df_processed[numeric_cols])
                reduced_cols = [f'PCA_{i+1}' for i in range(n_components)]
                df_processed = pd.concat([df_processed.drop(numeric_cols, axis=1), pd.DataFrame(reduced, columns=reduced_cols, index=df_processed.index)], axis=1)
                actions.append(f"Applied PCA reduction to {n_components} components")
            elif red_method == 'tsne':
                tsne = TSNE(n_components=n_components)
                reduced = tsne.fit_transform(df_processed[numeric_cols])
                reduced_cols = [f'TSNE_{i+1}' for i in range(n_components)]
                df_processed = pd.concat([df_processed.drop(numeric_cols, axis=1), pd.DataFrame(reduced, columns=reduced_cols, index=df_processed.index)], axis=1)
                actions.append(f"Applied t-SNE reduction to {n_components} components")
            elif red_method == 'svd':
                svd = TruncatedSVD(n_components=n_components)
                reduced = svd.fit_transform(df_processed[numeric_cols])
                reduced_cols = [f'SVD_{i+1}' for i in range(n_components)]
                df_processed = pd.concat([df_processed.drop(numeric_cols, axis=1), pd.DataFrame(reduced, columns=reduced_cols, index=df_processed.index)], axis=1)
                actions.append(f"Applied SVD reduction to {n_components} components")
            elif red_method == 'lda' and 'target_col' in params:
                lda = LDA(n_components=n_components)
                reduced = lda.fit_transform(df_processed[numeric_cols], df_processed[params['target_col']])
                reduced_cols = [f'LDA_{i+1}' for i in range(n_components)]
                df_processed = pd.concat([df_processed.drop(numeric_cols, axis=1), pd.DataFrame(reduced, columns=reduced_cols, index=df_processed.index)], axis=1)
                actions.append(f"Applied LDA reduction to {n_components} components")
        
        # 6. Feature Selection
        if params.get('feature_selection', False):
            sel_method = params.get('sel_method', 'variance')  # variance, kbest, rfe, importance
            if sel_method == 'variance':
                selector = VarianceThreshold(threshold=params.get('var_threshold', 0.0))
                df_processed[numeric_cols] = selector.fit_transform(df_processed[numeric_cols])
                selected_cols = [numeric_cols[i] for i in selector.get_support(indices=True)]
                df_processed = df_processed[selected_cols + categorical_cols]
                actions.append(f"Selected features with variance > {params.get('var_threshold', 0.0)}")
            elif sel_method == 'kbest' and 'target_col' in params:
                k = 'all' if params.get('k_best', 'all') == 'all' else int(params.get('k_best', 'all'))
                selector = SelectKBest(score_func=chi2, k=k)
                selector.fit(df_processed[numeric_cols], df_processed[params['target_col']])
                selected_cols = [numeric_cols[i] for i in selector.get_support(indices=True)]
                df_processed = df_processed[selected_cols + categorical_cols]
                actions.append(f"Selected top {k} features using chi2")
            elif sel_method == 'importance' and 'target_col' in params:
                model = RandomForestClassifier()
                model.fit(df_processed[numeric_cols], df_processed[params['target_col']])
                importances = model.feature_importances_
                threshold = params.get('imp_threshold', 0.01)
                selected = [col for col, imp in zip(numeric_cols, importances) if imp >= threshold]
                df_processed = df_processed[selected + categorical_cols]
                actions.append(f"Selected features with importance >= {threshold}")
        
        # 7. Handling Imbalanced Data
        if params.get('handle_imbalance', False) and 'target_col' in params:
            imb_method = params.get('imb_method', 'smote')  # smote, oversample, undersample
            X = df_processed.drop(params['target_col'], axis=1)
            y = df_processed[params['target_col']]
            if imb_method == 'smote':
                sampler = SMOTE()
            elif imb_method == 'undersample':
                sampler = RandomUnderSampler()
            X_res, y_res = sampler.fit_resample(X, y)
            df_processed = pd.concat([X_res, y_res], axis=1)
            actions.append(f"Applied {imb_method} for class imbalance")
        
        # 8. Feature Engineering (basic)
        if params.get('feature_engineering', False):
            if params.get('polynomial', False):
                from sklearn.preprocessing import PolynomialFeatures
                poly = PolynomialFeatures(degree=params.get('poly_degree', 2), include_bias=False)
                poly_features = poly.fit_transform(df_processed[numeric_cols])
                poly_cols = poly.get_feature_names_out(numeric_cols)
                df_processed = pd.concat([df_processed.drop(numeric_cols, axis=1), pd.DataFrame(poly_features, columns=poly_cols, index=df_processed.index)], axis=1)
                actions.append(f"Added polynomial features (degree {params.get('poly_degree', 2)})")
            if params.get('binning', False):
                for col in params.get('bin_cols', []):
                    df_processed[col + '_binned'] = pd.qcut(df_processed[col], q=params.get('bins', 5), labels=False)
                    actions.append(f"Binned {col} into {params.get('bins', 5)} bins")
        
        return df_processed, actions
    
    except Exception as e:
        st.error(f"Preprocessing error: {str(e)}")
        return df, [f"Failed: {str(e)}"]
    

def create_custom_plot(df: pd.DataFrame, plot_config: Dict[str, Any]) -> Tuple[any, str]:
    """Expanded custom plots with all types and better error handling"""
    try:
        plot_type = plot_config.get('type', 'auto').lower()
        x_col = plot_config.get('x')
        y_col = plot_config.get('y')
        z_col = plot_config.get('z')  # For 3D
        color_col = plot_config.get('color')
        size_col = plot_config.get('size')
        title = plot_config.get('title', f"{plot_type.title()} Plot")
        sample_df = df.sample(min(5000, len(df))) if len(df) > 5000 else df
        
        # Validate columns exist
        available_cols = sample_df.columns.tolist()
        if x_col and x_col not in available_cols:
            return None, f"Column '{x_col}' not found. Available: {available_cols[:10]}"
        if y_col and y_col not in available_cols:
            return None, f"Column '{y_col}' not found. Available: {available_cols[:10]}"
        if z_col and z_col not in available_cols:
            return None, f"Column '{z_col}' not found. Available: {available_cols[:10]}"
        if color_col and color_col not in available_cols:
            return None, f"Column '{color_col}' not found. Available: {available_cols[:10]}"
        
        # Auto plot generation
        if plot_type == 'auto':
            return generate_auto_plot(sample_df, title)
        
        # Clean data for plotting
        plot_cols = [col for col in [x_col, y_col, z_col, color_col, size_col] if col]
        clean_df = sample_df[plot_cols].dropna() if plot_cols else sample_df
        
        if len(clean_df) == 0:
            return None, "No data available after removing missing values"
        
        # Plotly types with better error handling
        fig = None
        if plot_type == 'scatter':
            fig = px.scatter(clean_df, x=x_col, y=y_col, color=color_col, size=size_col, title=title)
        elif plot_type == 'scatter3d':
            if not all([x_col, y_col, z_col]):
                return None, "3D scatter requires x, y, and z columns"
            fig = px.scatter_3d(clean_df, x=x_col, y=y_col, z=z_col, color=color_col, title=title)
        elif plot_type == 'line':
            fig = px.line(clean_df, x=x_col, y=y_col, color=color_col, title=title)
        elif plot_type == 'line3d':
            if not all([x_col, y_col, z_col]):
                return None, "3D line requires x, y, and z columns"
            fig = px.line_3d(clean_df, x=x_col, y=y_col, z=z_col, color=color_col, title=title)
        elif plot_type == 'bar':
            fig = px.bar(clean_df, x=x_col, y=y_col, color=color_col, title=title, 
                        barmode=plot_config.get('barmode', 'group'))
        elif plot_type == 'histogram':
            fig = px.histogram(clean_df, x=x_col, color=color_col, title=title, 
                             nbins=plot_config.get('nbins', 30))
        elif plot_type == 'box':
            fig = px.box(clean_df, x=x_col, y=y_col, color=color_col, title=title)
        elif plot_type == 'violin':
            fig = px.violin(clean_df, x=x_col, y=y_col, color=color_col, box=True, title=title)
        elif plot_type == 'heatmap':
            numeric_cols = sample_df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) >= 2:
                corr = sample_df[numeric_cols].corr()
                fig = px.imshow(corr, text_auto=True, title=title, color_continuous_scale='RdBu')
            else:
                return None, "Heatmap requires at least 2 numeric columns"
        elif plot_type == 'contour':
            if not all([x_col, y_col]):
                return None, "Contour plot requires x and y columns"
            fig = px.density_contour(clean_df, x=x_col, y=y_col, title=title)
        elif plot_type == 'pie':
            if not all([x_col, y_col]):
                return None, "Pie chart requires names (x) and values (y) columns"
            fig = px.pie(clean_df, values=y_col, names=x_col, title=title)
        elif plot_type == 'sunburst':
            path_cols = plot_config.get('path', [x_col] if x_col else [])
            if not path_cols or not y_col:
                return None, "Sunburst requires path and values columns"
            fig = px.sunburst(clean_df, path=path_cols, values=y_col, title=title)
        elif plot_type == 'treemap':
            path_cols = plot_config.get('path', [x_col] if x_col else [])
            if not path_cols or not y_col:
                return None, "Treemap requires path and values columns"
            fig = px.treemap(clean_df, path=path_cols, values=y_col, title=title)
        elif plot_type == 'waterfall':
            if not all([x_col, y_col]):
                return None, "Waterfall requires x and y columns"
            fig = go.Figure(go.Waterfall(
                name="", orientation="v",
                measure=["relative"] * len(clean_df),
                x=clean_df[x_col],
                textposition="outside",
                text=clean_df[y_col],
                y=clean_df[y_col],
                connector={"line": {"color": "rgb(63, 63, 63)"}},
            ))
            fig.update_layout(title=title)
        elif plot_type == 'surface':
            if not all([x_col, y_col, z_col]):
                return None, "Surface plot requires x, y, and z columns"
            # Reshape data for surface plot
            pivot_df = clean_df.pivot_table(values=z_col, index=y_col, columns=x_col, aggfunc='mean')
            fig = go.Figure(data=[go.Surface(z=pivot_df.values, x=pivot_df.columns, y=pivot_df.index)])
            fig.update_layout(title=title)
        
        # Seaborn integrations (use matplotlib backend for Streamlit)
        elif plot_type == 'pairplot':
            numeric_cols = clean_df.select_dtypes(include=[np.number]).columns[:4]  # Limit for performance
            if len(numeric_cols) < 2:
                return None, "Pairplot requires at least 2 numeric columns"
            pair_df = clean_df[numeric_cols]
            g = sns.pairplot(pair_df, diag_kind='hist')
            return g.fig, "Created Pairplot"
        elif plot_type == 'jointplot':
            if not all([x_col, y_col]):
                return None, "Jointplot requires x and y columns"
            g = sns.jointplot(data=clean_df, x=x_col, y=y_col, kind=plot_config.get('kind', 'scatter'))
            return g.fig, "Created Jointplot"
        elif plot_type == 'kdeplot':
            fig, ax = plt.subplots(figsize=(8, 6))
            if x_col and y_col:
                sns.kdeplot(data=clean_df, x=x_col, y=y_col, fill=True, ax=ax)
            elif x_col:
                sns.kdeplot(data=clean_df, x=x_col, fill=True, ax=ax)
            else:
                return None, "KDEplot requires at least x column"
            plt.title(title)
            return fig, "Created KDEplot"
        elif plot_type == 'distplot':
            if not x_col:
                return None, "Distplot requires x column"
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.histplot(clean_df[x_col], kde=True, ax=ax)  # distplot is deprecated
            plt.title(title)
            return fig, "Created Distribution plot"
        elif plot_type == 'catplot':
            if not x_col:
                return None, "Catplot requires x column"
            g = sns.catplot(data=clean_df, x=x_col, y=y_col, hue=color_col, 
                           kind=plot_config.get('kind', 'strip'))
            g.fig.suptitle(title)
            return g.fig, "Created Catplot"
        elif plot_type == 'countplot':
            if not x_col:
                return None, "Countplot requires x column"
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.countplot(data=clean_df, x=x_col, hue=color_col, ax=ax)
            plt.title(title)
            plt.xticks(rotation=45)
            return fig, "Created Countplot"
        else:
            return None, f"Unsupported plot type: {plot_type}"
        
        # Update layout for plotly figures
        if fig and hasattr(fig, 'update_layout'):
            fig.update_layout(height=500, showlegend=True)
        
        return fig, f"Created {plot_type} plot successfully"
    
    except Exception as e:
        return None, f"Plot creation failed: {str(e)}"

def generate_auto_plot(df: pd.DataFrame, title: str = "Auto Generated Plot") -> Tuple[any, str]:
    """Generate automatic plot based on data characteristics"""
    try:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        if len(numeric_cols) >= 2:
            # Correlation heatmap for multiple numeric columns
            corr = df[numeric_cols].corr()
            fig = px.imshow(corr, text_auto=True, title=f"{title} - Correlation Matrix",
                           color_continuous_scale='RdBu')
            return fig, "Generated correlation heatmap"
        elif len(numeric_cols) == 1:
            # Histogram for single numeric column
            fig = px.histogram(df, x=numeric_cols[0], title=f"{title} - Distribution")
            return fig, f"Generated histogram for {numeric_cols[0]}"
        elif len(categorical_cols) >= 1:
            # Bar chart for categorical data
            col = categorical_cols[0]
            if df[col].nunique() <= 20:  # Reasonable number of categories
                value_counts = df[col].value_counts().head(10)
                fig = px.bar(x=value_counts.index, y=value_counts.values,
                           title=f"{title} - {col} Distribution")
                return fig, f"Generated bar chart for {col}"
        
        return None, "Could not determine appropriate plot for this data"
    except Exception as e:
        return None, f"Auto plot generation failed: {str(e)}"

# --- ENHANCED LangGraph Agent Setup ---

if LANGGRAPH_AVAILABLE and GENAI:
    try:
        @tool
        def analyze_data_tool(file_reference: str) -> str:
            """Analyze dataset and provide insights"""
            df, name, idx = get_file_by_ref(file_reference)
            if df is None:
                return f"File {file_reference} not found"
            profile = generate_data_profile(df)
            insights = []
            insights.append(f"📊 Dataset: {name}")
            insights.append(f"📏 Shape: {profile['shape'][0]:,} rows × {profile['shape'][1]} columns")
            insights.append(f"💾 Memory: {profile['memory_usage'] / 1024**2:.1f} MB")
            insights.append(f"🔍 Data Quality Score: {profile['data_quality_score']:.1f}/100")
            if profile['missing_values']:
                missing_cols = [col for col, count in profile['missing_values'].items() if count > 0]
                if missing_cols:
                    insights.append(f"⚠️ Missing data in: {', '.join(missing_cols[:5])}")
            if profile['duplicate_rows'] > 0:
                insights.append(f"🔄 Duplicate rows: {profile['duplicate_rows']:,}")
            return "\n".join(insights)

        @tool
        def preprocess_data_tool(file_reference: str,
                         missing_strategy: str = "mean",  # Add: knn, iterative, drop
                         cat_missing_strategy: str = "mode",  # mode, constant
                         constant_value: str = "Unknown",
                         knn_neighbors: int = 5,
                         iter_max: int = 10,
                         handle_outliers: bool = True,
                         outlier_method: str = "iqr",  # Add: isolation_forest
                         outlier_action: str = "cap",  # Add: transform
                         transform_method: str = "yeo-johnson",
                         contamination: float = 0.05,
                         scale_type: str = "none",  # minmax, standard, robust
                         encode_categoricals: bool = False,
                         encode_method: str = "onehot",  # Add: ordinal, binary, frequency, target
                         max_categories: int = 10,
                         target_col: str = None,  # For target encoding/LDA
                         reduce_dimensions: bool = False,
                         red_method: str = "pca",  # pca, tsne, svd, lda
                         n_components: int = 2,
                         feature_selection: bool = False,
                         sel_method: str = "variance",  # variance, kbest, importance
                         var_threshold: float = 0.0,
                         k_best: str = "all",
                         imp_threshold: float = 0.01,
                         handle_imbalance: bool = False,
                         imb_method: str = "smote",  # smote, undersample
                         feature_engineering: bool = False,
                         polynomial: bool = False,
                         poly_degree: int = 2,
                         binning: bool = False,
                         bin_cols: str = None,
                         bins: int = 5) -> str:
            """Comprehensive preprocessing with all parameters"""
            df, name, idx = get_file_by_ref(file_reference)
            if df is None:
                return f"File {file_reference} not found"
            
            # Parse comma-separated bin_cols if provided
            bin_cols_parsed = bin_cols.split(',') if bin_cols and isinstance(bin_cols, str) else None
            # Parse k_best if it's numeric
            try:
                k_best_parsed = int(k_best) if k_best and k_best != "all" else k_best
            except:
                k_best_parsed = k_best
            
            processing_params = {
                # Pass all new params here...
                "handle_missing": True,
                "missing_strategy": missing_strategy,
                "cat_missing_strategy": cat_missing_strategy,
                "constant_value": constant_value,
                "knn_neighbors": knn_neighbors,
                "iter_max": iter_max,
                "handle_outliers": handle_outliers,
                "outlier_method": outlier_method,
                "outlier_action": outlier_action,
                "transform_method": transform_method,
                "contamination": contamination,
                "scale_type": scale_type,
                "encode_categoricals": encode_categoricals,
                "encode_method": encode_method,
                "max_categories": max_categories,
                "target_col": target_col,
                "reduce_dimensions": reduce_dimensions,
                "red_method": red_method,
                "n_components": n_components,
                "feature_selection": feature_selection,
                "sel_method": sel_method,
                "var_threshold": var_threshold,
                "k_best": k_best_parsed,
                "imp_threshold": imp_threshold,
                "handle_imbalance": handle_imbalance,
                "imb_method": imb_method,
                "feature_engineering": feature_engineering,
                "polynomial": polynomial,
                "poly_degree": poly_degree,
                "binning": binning,
                "bin_cols": bin_cols_parsed,
                "bins": bins
            }
            processed_df, actions = enhanced_preprocessing(df, processing_params)
            timestamp = int(time.time())
            processed_name = f"preprocessed_{name.split('.')[0]}_{timestamp}.csv"
            st.session_state.preprocessed_files[processed_name] = processed_df
            history = ProcessingHistory(
                action="comprehensive_preprocessing",
                params=processing_params,
                timestamp=datetime.now().isoformat(),
                result_shape=processed_df.shape,
                success=True,
                message=f"Applied {len(actions)} steps"
            )
            st.session_state.processing_history.append(history)
            result_msg = f"✅ PREPROCESSING COMPLETE!\n\nOriginal shape: {df.shape}\nNew shape: {processed_df.shape}\n\nACTIONS:\n" + "\n".join([f"{i+1}. {a}" for i, a in enumerate(actions)])
            result_msg += f"\n💾 File: {processed_name} ready in Results tab"
            return result_msg

        @tool
        def create_visualization_tool(file_reference: str,
                              plot_type: str = "auto",
                              x_column: str = None,
                              y_column: str = None,
                              z_column: str = None,
                              color_column: str = None,
                              size_column: str = None,
                              barmode: str = "group",
                              nbins: int = 30,
                              kind: str = "scatter",
                              path: str = None,
                              locationmode: str = "country names",
                              fill: bool = True
                              ) -> str:
            """Create any visualization type with improved error handling"""
            try:
                df, name, idx = get_file_by_ref(file_reference)
                if df is None:
                    return f"❌ File {file_reference} not found"
                
                # Show available columns for context
                available_cols = df.columns.tolist()
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                
                if plot_type == "auto":
                    plots = create_smart_visualizations(df, max_plots=8)
                    if plots:
                        cache_key = f"auto_{idx}_{int(time.time())}"
                        st.session_state.plot_cache[cache_key] = plots
                        return f"✅ Generated {len(plots)} auto visualizations for {name}!\n📊 Created: {', '.join([p[0] for p in plots[:3]])}{'...' if len(plots) > 3 else ''}\n👀 View all plots in Results tab."
                    else:
                        return f"❌ Could not generate auto plots for {name}. Try specifying columns manually."
                else:
                    # Validate and suggest columns if not provided
                    suggestions = []
                    if not x_column and plot_type in ['scatter', 'line', 'bar', 'histogram', 'box', 'violin']:
                        if numeric_cols:
                            suggestions.append(f"Suggested x columns: {', '.join(numeric_cols[:3])}")
                        elif categorical_cols:
                            suggestions.append(f"Suggested x columns: {', '.join(categorical_cols[:3])}")
                    
                    # Parse path parameter if it's a comma-separated string
                    path_parsed = path.split(',') if path and isinstance(path, str) else (path if path else [])
                    
                    plot_config = {
                        'type': plot_type,
                        'x': x_column,
                        'y': y_column,
                        'z': z_column,
                        'color': color_column,
                        'size': size_column,
                        'barmode': barmode,
                        'nbins': nbins,
                        'kind': kind,
                        'path': path_parsed,
                        'locationmode': locationmode,
                        'fill': fill,
                        'title': f"{plot_type.title()} - {name}"
                    }
                    
                    fig, msg = create_custom_plot(df, plot_config)
                    if fig:
                        cache_key = f"custom_{plot_type}_{int(time.time())}"
                        st.session_state.plot_cache[cache_key] = [(f"{plot_type.title()} Plot", fig)]
                        result = f"✅ Created {plot_type} plot successfully!\n📊 {msg}\n👀 View in Results tab."
                        if suggestions:
                            result += f"\n💡 {' | '.join(suggestions)}"
                        return result
                    else:
                        error_msg = f"❌ Failed to create {plot_type} plot: {msg}"
                        if suggestions:
                            error_msg += f"\n💡 {' | '.join(suggestions)}"
                        error_msg += f"\n📋 Available columns: {', '.join(available_cols[:10])}{'...' if len(available_cols) > 10 else ''}"
                        return error_msg
                        
            except Exception as e:
                return f"❌ Visualization tool error: {str(e)}"

        @tool
        def merge_files_tool(left_file: str, right_file: str, 
                     how: str = "inner",  # inner, outer, left, right, cross
                     left_on: str = None,
                     right_on: str = None, 
                     suffixes: str = "_left,_right",
                     indicator: bool = False,
                     validate: str = None,  # one_to_one, etc.
                     fuzzy: bool = False,
                     fuzzy_threshold: int = 80,
                     concat_axis: int = None,
                     join: str = "outer",  # For concat
                     keys: str = None) -> str:
            """Comprehensive merging"""
            left_df, left_name, _ = get_file_by_ref(left_file)
            right_df, right_name, _ = get_file_by_ref(right_file)
            if left_df is None or right_df is None:
                return "File not found"
            
            # Parse parameters
            left_on_parsed = left_on.split(',') if left_on and ',' in left_on else left_on
            right_on_parsed = right_on.split(',') if right_on and ',' in right_on else right_on
            suffixes_parsed = suffixes.split(',') if suffixes and ',' in suffixes else ["_left", "_right"]
            
            merged_df, msg = merge_dataframes(left_df, right_df, left_on=left_on_parsed, right_on=right_on_parsed, how=how, concat_axis=concat_axis, suffixes=suffixes_parsed, indicator=indicator, validate=validate, fuzzy=fuzzy, fuzzy_threshold=fuzzy_threshold)
            if merged_df is not None:
                timestamp = int(time.time())
                merged_name = f"merged_{left_name.split('.')[0]}_{right_name.split('.')[0]}_{timestamp}.csv"
                st.session_state.preprocessed_files[merged_name] = merged_df
                return f"SUCCESS: {msg}\nShape: {merged_df.shape}\nSaved as: {merged_name}"
            else:
                return f"Failed: {msg}"

        # Agent state
        class AgentState(dict):
            messages: List[Any]
            current_task: str
            files_context: Dict[str, Any]
            results: List[str]

        def create_eda_agent():
            """Create the autonomous EDA agent with LangGraph"""
            tools = [analyze_data_tool, preprocess_data_tool, create_visualization_tool, merge_files_tool]

            def agent_node(state: AgentState):
                messages = state["messages"]
                # Prepare context about available files
                files_context = ""
                for idx, file_data in st.session_state.files.items():
                    metadata = file_data["metadata"]
                    files_context += f"File {idx}: {metadata.name} ({metadata.shape[0]}x{metadata.shape[1]})\n"
                # AUTONOMOUS AGENT SYSTEM PROMPT
                system_prompt = f"""
You are an AUTONOMOUS EDA agent that EXECUTES tasks immediately.
AVAILABLE FILES:
{files_context}

YOUR BEHAVIOR:
- When the user requests data operations (analysis, preprocessing, visualization, merging), call the appropriate tool.
- After receiving tool results, provide a brief, friendly summary of what was accomplished.
- If the user asks a question about past actions, answer directly without calling tools.
- Be concise and action-oriented.

IMPORTANT: After tool execution, ALWAYS provide a short summary message to the user confirming what was done.

TOOL MAPPING:
- Data analysis/insights → analyze_data_tool
- Preprocessing requests → preprocess_data_tool (with all advanced parameters)
- Visualization requests → create_visualization_tool (with all advanced plot options)
- Data merging → merge_files_tool (with all advanced merge options)

PREPROCESSING PARAMETERS (FULL):
- missing_strategy: mean, median, mode, knn, iterative, drop
- cat_missing_strategy: mode, constant
- constant_value: str
- knn_neighbors: int
- iter_max: int
- handle_outliers: true/false
- outlier_method: iqr, zscore, isolation_forest
- outlier_action: cap, remove, transform
- transform_method: yeo-johnson, box-cox
- contamination: float
- scale_type: none, minmax, standard, robust
- encode_categoricals: true/false
- encode_method: onehot, label, ordinal, binary, frequency, target
- max_categories: int
- target_col: str
- reduce_dimensions: true/false
- red_method: pca, tsne, svd, lda
- n_components: int
- feature_selection: true/false
- sel_method: variance, kbest, importance
- var_threshold: float
- k_best: int or 'all'
- imp_threshold: float
- handle_imbalance: true/false
- imb_method: smote, undersample
- feature_engineering: true/false
- polynomial: true/false
- poly_degree: int
- binning: true/false
- bin_cols: list of str
- bins: int

VISUALIZATION PARAMETERS (FULL):
- plot_type: auto, scatter, scatter3d, line, line3d, bar, barpolar, histogram, box, violin, heatmap, contour, pie, sunburst, treemap, funnel, waterfall, choropleth, surface, mesh3d, pairplot, jointplot, kdeplot, distplot, catplot, facetgrid, relplot, lmplot, countplot, stripplot, swarmplot, pointplot, boxenplot, clustermap
- x_column, y_column, z_column, color_column, size_column, barmode, nbins, kind, path, locationmode, fill

MERGING PARAMETERS (FULL):
- how: inner, outer, left, right, cross
- left_on, right_on: str or list of str
- suffixes: list
- indicator: true/false
- validate: str
- fuzzy: true/false
- fuzzy_threshold: int
- concat_axis: int
- join: str
- keys: list of str

EXAMPLE USER REQUESTS:
\"analyze file 0\" → call analyze_data_tool(\"0\")
\"fill missing values with mean, use knn for categoricals, cap outliers with isolation forest, minmax scale, onehot encode, reduce dimensions with PCA to 2, select features by variance, handle imbalance with SMOTE, add polynomial features degree 2, bin age column into 5 bins\" → call preprocess_data_tool with all params
\"create scatter3d plot for file 1 with x=age, y=income, z=score, color=gender\" → call create_visualization_tool(\"1\", \"scatter3d\", ...)
\"merge files 0 and 1 on id column with fuzzy matching threshold 90\" → call merge_files_tool(\"0\", \"1\", left_on=\"id\", right_on=\"id\", fuzzy=True, fuzzy_threshold=90)
\"what preprocessing did you use on file 0?\" → answer directly: \"Filled missing with mean, used knn for categoricals, capped outliers with isolation forest, applied minmax scaling, onehot encoded, reduced dimensions with PCA, selected features by variance, handled imbalance with SMOTE, added polynomial features, binned age column.\"
Execute or respond immediately. No extra explanations.
"""
                try:
                    llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    google_api_key=os.getenv("GOOGLE_API_KEY"),
                    )
                    full_messages = [
                    SystemMessage(content=system_prompt)
                    ] + messages
                    response = llm.bind_tools(tools).invoke(full_messages)
                    return {"messages": messages + [response]}
                except Exception as e:
                    error_response = AIMessage(content=f"❌ Agent error: {str(e)}")
                    return {"messages": messages + [error_response]}

            def tool_node(state: AgentState):
                """Execute tools based on the last message"""
                messages = state["messages"]
                last_message = messages[-1]
                if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                    tool_results = []
                    tool_messages = []
                    for tool_call in last_message.tool_calls:
                        try:
                            tool_name = tool_call["name"]
                            tool_args = tool_call["args"]
                            if tool_name == "analyze_data_tool":
                                result = analyze_data_tool.invoke(tool_args)
                            elif tool_name == "preprocess_data_tool":
                                result = preprocess_data_tool.invoke(tool_args)
                            elif tool_name == "create_visualization_tool":
                                result = create_visualization_tool.invoke(tool_args)
                            elif tool_name == "merge_files_tool":
                                result = merge_files_tool.invoke(tool_args)
                            else:
                                result = f"❌ Unknown tool: {tool_name}"
                            tool_results.append(result)
                            # Create ToolMessage for proper sequencing
                            tool_messages.append(
                                ToolMessage(
                                content=result,
                                tool_call_id=tool_call["id"]
                            )
                        )
                        except Exception as e:
                            error_result = f"❌ Tool execution error: {str(e)}"
                            tool_results.append(error_result)
                            tool_messages.append(
                                ToolMessage(
                                    content=error_result,
                                    tool_call_id=tool_call["id"]
                                )
                            )
                    return {"messages": messages + tool_messages}
                return {"messages": messages}
            
            workflow = StateGraph(AgentState)
            workflow.add_node("agent", agent_node)
            workflow.add_node("tools", tool_node)
            workflow.set_entry_point("agent")
            workflow.add_conditional_edges(
                "agent",
                lambda x: "tools" if hasattr(x["messages"][-1], 'tool_calls') and x["messages"][-1].tool_calls else END,
            )
            workflow.add_edge("tools", "agent")
            return workflow.compile()

        LANGGRAPH_AGENT = create_eda_agent()
    except Exception as e:
        st.warning(f"LangGraph setup failed: {e}. Using fallback mode.")
        LANGGRAPH_AVAILABLE = False

# --- Streamlit UI ---

# Header
st.markdown("""
<div class="main-header">
    <h1>🤖 Autonomous EDA Agent</h1>
    <p>Upload datasets • Chat with AI • Get instant results automatically</p>
</div>
""", unsafe_allow_html=True)

# Sidebar - File Management
st.sidebar.title("📁 File Manager")

# File upload
uploaded_files = st.sidebar.file_uploader(
    "Upload CSV/Excel files",
    type=['csv', 'xlsx', 'xls'],
    accept_multiple_files=True,
    help="Upload multiple files for analysis and merging"
)

if uploaded_files:
    for uploaded_file in uploaded_files:
        if uploaded_file.name not in [file_data["metadata"].name for file_data in st.session_state.files.values()]:
            with st.spinner(f"Loading {uploaded_file.name}..."):
                df = load_file_buffer(uploaded_file)
                if df is not None:
                    idx = add_file(df, uploaded_file.name)
                    st.sidebar.success(f"✅ Loaded: {uploaded_file.name} (ID: {idx})")
                    
                    # AWS: Upload to S3 and track in DynamoDB/CloudWatch
                    if AWS_AVAILABLE:
                        try:
                            import uuid as _uuid
                            file_id = str(_uuid.uuid4())
                            user_id = st.session_state.get("user_id", "anonymous")
                            
                            # Upload to S3
                            if s3_storage and s3_storage.available:
                                uploaded_file.seek(0)
                                s3_key = f"{user_id}/{file_id}_{uploaded_file.name}"
                                success, key_or_err = s3_storage.upload_file(
                                    uploaded_file.read(), s3_key)
                                if success:
                                    st.session_state.files[idx]["s3_key"] = s3_key
                            
                            # Track in DynamoDB
                            if dynamo_db and dynamo_db.available:
                                dynamo_db.save_file_metadata(
                                    user_id=user_id,
                                    file_id=file_id,
                                    filename=uploaded_file.name,
                                    file_path=st.session_state.files[idx].get("s3_key", ""),
                                    file_size=st.session_state.files[idx]["metadata"].file_size,
                                    rows=df.shape[0],
                                    columns=df.shape[1],
                                    s3_key=st.session_state.files[idx].get("s3_key", "")
                                )
                            
                            # CloudWatch metric
                            if cw_logger and cw_logger.available:
                                cw_logger.track_file_upload(
                                    uploaded_file.name,
                                    st.session_state.files[idx]["metadata"].file_size
                                )
                        except Exception as aws_err:
                            print(f"AWS tracking error (non-fatal): {aws_err}")

# Display uploaded files
if st.session_state.files:
    st.sidebar.markdown("### 📊 Loaded Files")
    for idx, file_data in st.session_state.files.items():
        metadata = file_data["metadata"]
        with st.sidebar.expander(f"📄 {idx}: {metadata.name}"):
            st.write(f"**Shape:** {metadata.shape[0]:,} × {metadata.shape[1]}")
            st.write(f"**Size:** {metadata.file_size / 1024**2:.1f} MB")
            st.write(f"**Uploaded:** {metadata.uploaded_at[:19]}")
            
            if st.button(f"🗑️ Remove", key=f"remove_{idx}"):
                del st.session_state.files[idx]
                if st.session_state.last_idx == idx:
                    st.session_state.last_idx = max(st.session_state.files.keys(), default=None)
                st.rerun()

# Main content tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Overview", "🛠️ Tools", "🤖 AI Chat", "📊 Results", "📈 Reports"])

with tab1:
    st.header("📋 Dataset Overview")
    
    if not st.session_state.files:
        st.info("👆 Upload files using the sidebar to get started!")
        st.markdown("""
        ### What you can do with the Autonomous Agent:
        - **Upload multiple CSV/Excel files** 
        - **Chat naturally:** "fill missing values with mean and do outlier analysis, min max scaling and one hot encoding"
        - **Get instant results** - no code writing needed!
        - **Download processed files** immediately
        - **Merge datasets** intelligently
        - **Generate visualizations** automatically
        """)
    else:
        # Quick stats
        total_rows = sum(file_data["metadata"].shape[0] for file_data in st.session_state.files.values())
        total_cols = sum(file_data["metadata"].shape[1] for file_data in st.session_state.files.values())
        total_size = sum(file_data["metadata"].file_size for file_data in st.session_state.files.values())
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📁 Files", len(st.session_state.files))
        with col2:
            st.metric("📏 Total Rows", f"{total_rows:,}")
        with col3:
            st.metric("🔢 Total Columns", total_cols)
        with col4:
            st.metric("💾 Total Size", f"{total_size / 1024**2:.1f} MB")
        
        # File details
        st.subheader("📊 File Details")
        for idx, file_data in st.session_state.files.items():
            metadata = file_data["metadata"]
            df = file_data["df"]
            
            with st.expander(f"📄 File {idx}: {metadata.name}", expanded=(idx == st.session_state.last_idx)):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Shape:** {metadata.shape[0]:,} rows × {metadata.shape[1]} columns")
                    st.markdown(f"**Memory:** {metadata.file_size / 1024**2:.1f} MB")
                    
                    # Data types
                    dtype_counts = pd.Series(list(metadata.dtypes.values())).value_counts()
                    st.markdown("**Data Types:**")
                    for dtype, count in dtype_counts.items():
                        st.markdown(f"  - {dtype}: {count} columns")
                    
                    # Missing data
                    missing_total = sum(metadata.missing_count.values())
                    if missing_total > 0:
                        st.markdown(f"**Missing Values:** {missing_total:,} total")
                        missing_cols = [col for col, count in metadata.missing_count.items() if count > 0]
                        st.markdown(f"  - Affected columns: {', '.join(missing_cols[:5])}")
                        if len(missing_cols) > 5:
                            st.markdown(f"  - ... and {len(missing_cols)-5} more")
                
                with col2:
                    if st.button(f"🔍 Quick Analysis", key=f"analyze_{idx}"):
                        with st.spinner("Analyzing..."):
                            profile = generate_data_profile(df)
                            st.session_state[f"profile_{idx}"] = profile
                    
                    if st.button(f"📊 Auto Visualize", key=f"viz_{idx}"):
                        with st.spinner("Creating plots..."):
                            plots = create_smart_visualizations(df, max_plots=3)
                            if plots:
                                st.session_state.plot_cache[f"auto_{idx}"] = plots
                                st.success(f"Generated {len(plots)} plots!")
                            else:
                                st.warning("Could not generate plots")
                
                # Show data preview
                st.markdown("**Data Preview:**")
                st.dataframe(df.head(), use_container_width=True)
                
                # Show analysis if available
                if f"profile_{idx}" in st.session_state:
                    profile = st.session_state[f"profile_{idx}"]
                    st.markdown(f"**Data Quality Score:** {profile['data_quality_score']:.1f}/100")

with tab2:
    st.header("🛠️ Interactive Tools")
    
    if not st.session_state.files:
        st.info("Upload files first to use tools!")
    else:
        # Quick Actions
        st.subheader("⚡ Quick Actions")
        st.markdown("*Use these buttons for instant preprocessing with common settings*")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🧹 Smart Clean", help="Fill missing values, handle outliers, basic preprocessing"):
                if st.session_state.last_idx is not None:
                    with st.spinner("Processing..."):
                        df, name, idx = get_file_by_ref(st.session_state.last_idx)
                        params = {
                            "handle_missing": True,
                            "missing_strategy": "mean",
                            "handle_outliers": True,
                            "outlier_action": "cap"
                        }
                        processed_df, actions = enhanced_preprocessing(df, params)
                        processed_name = f"smart_cleaned_{name.split('.')[0]}_{int(time.time())}.csv"
                        st.session_state.preprocessed_files[processed_name] = processed_df
                        st.success(f"✅ Smart cleaning complete! File: {processed_name}")
        
        with col2:
            if st.button("📊 Full Preprocess", help="Complete preprocessing pipeline"):
                if st.session_state.last_idx is not None:
                    with st.spinner("Processing..."):
                        df, name, idx = get_file_by_ref(st.session_state.last_idx)
                        params = {
                            "handle_missing": True,
                            "missing_strategy": "mean",
                            "handle_outliers": True,
                            "min_max_scale": True,
                            "one_hot_encode": True
                        }
                        processed_df, actions = enhanced_preprocessing(df, params)
                        processed_name = f"full_preprocessed_{name.split('.')[0]}_{int(time.time())}.csv"
                        st.session_state.preprocessed_files[processed_name] = processed_df
                        st.success(f"✅ Full preprocessing complete! File: {processed_name}")
        
        with col3:
            if st.button("📈 Auto Visualize All", help="Generate plots for the latest file"):
                if st.session_state.last_idx is not None:
                    with st.spinner("Creating visualizations..."):
                        df, name, idx = get_file_by_ref(st.session_state.last_idx)
                        plots = create_smart_visualizations(df, max_plots=6)
                        if plots:
                            cache_key = f"auto_all_{idx}_{int(time.time())}"
                            st.session_state.plot_cache[cache_key] = plots
                            st.success(f"✅ Generated {len(plots)} visualizations!")
                        else:
                            st.warning("Could not generate plots")
        
        st.markdown("---")
        
        # Advanced Tools (keeping your existing tools but simplified)
        tool_option = st.selectbox(
            "🔧 Advanced Tools",
            ["Custom Preprocessing", "Data Merger", "Plot Generator"]
        )
        
        if tool_option == "Custom Preprocessing":
            st.markdown('<div class="tool-card">', unsafe_allow_html=True)
            st.subheader("🧹 Custom Preprocessing")
            
            selected_file = st.selectbox(
                "Select Dataset",
                options=list(st.session_state.files.keys()),
                format_func=lambda x: f"File {x}: {st.session_state.files[x]['metadata'].name}"
            )
            

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Missing Values**")
                handle_missing = st.checkbox("Handle Missing", value=True)
                missing_strategy = st.selectbox("Strategy", ["mean", "median", "mode", "knn", "iterative", "drop"])
                cat_missing_strategy = st.selectbox("Cat Missing", ["mode", "constant"])
                constant_value = st.text_input("Constant Value", value="Unknown")
            with col2:
                st.markdown("**Outliers**")
                handle_outliers = st.checkbox("Handle Outliers", value=True)
                outlier_method = st.selectbox("Method", ["iqr", "zscore", "isolation_forest"])
                outlier_action = st.selectbox("Action", ["cap", "remove", "transform"])
                transform_method = st.selectbox("Transform Method", ["yeo-johnson", "box-cox"])
                contamination = st.number_input("Contamination", min_value=0.0, max_value=1.0, value=0.05)
            with col3:
                st.markdown("**Scaling & Encoding**")
                scale_type = st.selectbox("Scale Type", ["none", "minmax", "standard", "robust"])
                encode_categoricals = st.checkbox("Encode Categoricals", value=False)
                encode_method = st.selectbox("Encode Method", ["onehot", "label", "ordinal", "binary", "frequency", "target"])
                max_categories = st.number_input("Max Categories", min_value=2, max_value=100, value=10)

            col4, col5 = st.columns(2)
            with col4:
                st.markdown("**Dimensionality Reduction & Feature Selection**")
                reduce_dimensions = st.checkbox("Reduce Dimensions", value=False)
                red_method = st.selectbox("Reduction Method", ["pca", "tsne", "svd", "lda"])
                n_components = st.number_input("Components", min_value=1, max_value=50, value=2)
                feature_selection = st.checkbox("Feature Selection", value=False)
                sel_method = st.selectbox("Selection Method", ["variance", "kbest", "importance"])
                var_threshold = st.number_input("Variance Threshold", min_value=0.0, max_value=1.0, value=0.0)
                k_best = st.text_input("K Best", value="all")
                imp_threshold = st.number_input("Importance Threshold", min_value=0.0, max_value=1.0, value=0.01)
            with col5:
                st.markdown("**Imbalance & Feature Engineering**")
                handle_imbalance = st.checkbox("Handle Imbalance", value=False)
                imb_method = st.selectbox("Imbalance Method", ["smote", "undersample"])
                feature_engineering = st.checkbox("Feature Engineering", value=False)
                polynomial = st.checkbox("Polynomial Features", value=False)
                poly_degree = st.number_input("Poly Degree", min_value=2, max_value=10, value=2)
                binning = st.checkbox("Binning", value=False)
                bin_cols = st.text_input("Bin Columns (comma-separated)", value="")
                bins = st.number_input("Bins", min_value=2, max_value=50, value=5)
            
            if st.button("🚀 Process Data"):
                df, name, idx = get_file_by_ref(selected_file)
                
                params = {
                    "handle_missing": handle_missing,
                    "missing_strategy": missing_strategy,
                    "cat_missing_strategy": cat_missing_strategy,
                    "constant_value": constant_value,
                    "handle_outliers": handle_outliers,
                    "outlier_method": outlier_method,
                    "outlier_action": outlier_action,
                    "transform_method": transform_method,
                    "contamination": contamination,
                    "scale_type": scale_type,
                    "encode_categoricals": encode_categoricals,
                    "encode_method": encode_method,
                    "max_categories": max_categories,
                    "reduce_dimensions": reduce_dimensions,
                    "red_method": red_method,
                    "n_components": n_components,
                    "feature_selection": feature_selection,
                    "sel_method": sel_method,
                    "var_threshold": var_threshold,
                    "k_best": k_best,
                    "imp_threshold": imp_threshold,
                    "handle_imbalance": handle_imbalance,
                    "imb_method": imb_method,
                    "feature_engineering": feature_engineering,
                    "polynomial": polynomial,
                    "poly_degree": poly_degree,
                    "binning": binning,
                    "bin_cols": [col.strip() for col in bin_cols.split(",") if col.strip()],
                    "bins": bins
                }
                
                with st.spinner("Processing..."):
                    processed_df, actions = enhanced_preprocessing(df, params)
                    processed_name = f"custom_processed_{name.split('.')[0]}_{int(time.time())}.csv"
                    st.session_state.preprocessed_files[processed_name] = processed_df
                    
                    st.success(f"✅ Processing complete! File: {processed_name}")
                    st.markdown("**Actions performed:**")
                    for action in actions:
                        st.markdown(f"- {action}")
            
            st.markdown('</div>', unsafe_allow_html=True)

        if tool_option == "Plot Generator":
            st.markdown('<div class="tool-card">', unsafe_allow_html=True)
            st.subheader("📊 Plot Generator")
            
            selected_file = st.selectbox(
                "Select Dataset",
                options=list(st.session_state.files.keys()),
                format_func=lambda x: f"File {x}: {st.session_state.files[x]['metadata'].name}",
                key="plot_gen_file"
            )
            
            if selected_file is not None:
                df, name, idx = get_file_by_ref(selected_file)
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                all_cols = df.columns.tolist()
                
                st.info(f"📊 Available: {len(numeric_cols)} numeric, {len(categorical_cols)} categorical columns")
                
                col1, col2 = st.columns(2)
                with col1:
                    plot_type = st.selectbox("Plot Type", [
                        "auto", "scatter", "scatter3d", "line", "bar", "histogram", "box", "violin", 
                        "heatmap", "contour", "pie", "sunburst", "treemap", "waterfall",
                        "pairplot", "jointplot", "kdeplot", "countplot"
                    ])
                    
                    x_col = st.selectbox("X Column", [""] + all_cols, key="plot_x")
                    y_col = st.selectbox("Y Column", [""] + all_cols, key="plot_y")
                
                with col2:
                    z_col = st.selectbox("Z Column (3D only)", [""] + numeric_cols, key="plot_z")
                    color_col = st.selectbox("Color Column", [""] + all_cols, key="plot_color")
                    size_col = st.selectbox("Size Column", [""] + numeric_cols, key="plot_size")
                    
                    # Advanced options
                    with st.expander("Advanced Options"):
                        barmode = st.selectbox("Bar Mode", ["group", "stack", "overlay"])
                        nbins = st.slider("Histogram Bins", 10, 100, 30)
                        title = st.text_input("Custom Title", value=f"{plot_type.title()} - {name}")
                
                if st.button("🎨 Generate Plot", type="primary"):
                    plot_config = {
                        'type': plot_type,
                        'x': x_col if x_col else None,
                        'y': y_col if y_col else None,
                        'z': z_col if z_col else None,
                        'color': color_col if color_col else None,
                        'size': size_col if size_col else None,
                        'barmode': barmode,
                        'nbins': nbins,
                        'title': title
                    }
                    
                    with st.spinner("Creating plot..."):
                        fig, msg = create_custom_plot(df, plot_config)
                        if fig:
                            # Display the plot
                            if hasattr(fig, 'update_layout'):  # Plotly figure
                                st.plotly_chart(fig, use_container_width=True)
                            else:  # Matplotlib figure
                                st.pyplot(fig)
                            
                            # Cache the plot
                            cache_key = f"manual_{plot_type}_{int(time.time())}"
                            st.session_state.plot_cache[cache_key] = [(f"{plot_type.title()} Plot", fig)]
                            
                            st.success(f"✅ {msg}")
                            st.info("💾 Plot saved to Results tab for download")
                        else:
                            st.error(f"❌ {msg}")
                            
                            # Provide helpful suggestions
                            if plot_type in ['scatter', 'line'] and not x_col:
                                st.info(f"💡 Try selecting an X column from: {', '.join(numeric_cols[:5])}")
                            elif plot_type in ['bar', 'countplot'] and not x_col:
                                st.info(f"💡 Try selecting an X column from: {', '.join(categorical_cols[:5])}")
                            elif plot_type == 'heatmap' and len(numeric_cols) < 2:
                                st.info("💡 Heatmap requires at least 2 numeric columns")
            
            st.markdown('</div>', unsafe_allow_html=True)

        if tool_option == "Data Merger":
            st.subheader("🔗 Data Merger")
            left_file = st.selectbox("Left File", options=list(st.session_state.files.keys()))
            right_file = st.selectbox("Right File", options=list(st.session_state.files.keys()))
            how = st.selectbox("Merge Type", ["inner", "outer", "left", "right", "cross"])
            left_on = st.multiselect("Left Keys", st.session_state.files[int(left_file)]['df'].columns if left_file is not None else [])
            right_on = st.multiselect("Right Keys", st.session_state.files[int(right_file)]['df'].columns if right_file is not None else [])
            fuzzy = st.checkbox("Fuzzy Matching")
            if st.button("Merge"):
                merged_df, msg = merge_dataframes(
                    st.session_state.files[int(left_file)]['df'],
                    st.session_state.files[int(right_file)]['df'],
                    left_on=left_on,
                    right_on=right_on,
                    how=how,
                    fuzzy=fuzzy
                )
                if merged_df is not None:
                    add_file(merged_df, f"merged_{left_file}_{right_file}.csv")
                    st.success(msg)

# --- AI Chat Tab ---
with tab3:
    st.header("🤖 Autonomous AI Agent")
    
    if not st.session_state.files:
        st.info("Upload files first to start chatting with the AI!")
    else:
        # Prominent usage examples
        st.markdown("""
        ### 💡 Try these commands:
        - **"fill missing values with mean and do outlier analysis, min max scaling and one hot encoding"**
        - **"analyze file 0 and show insights"**
        - **"create visualizations for the latest file"**  
        - **"merge files 0 and 1"**
        - **"preprocess file 0 with median for missing values and standard scaling"**
        """)
        
        # Chat input
        user_input = st.text_area(
            "Chat with your autonomous agent:",
            height=120,
            placeholder="Just tell me what you want to do with your data - I'll execute it immediately!"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            send_button = st.button("🚀 Execute", type="primary")
        
        if send_button and user_input.strip():
            # Add user message to history
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now().isoformat()
            })
            
            with st.spinner("🤖 Agent is working..."):
                if LANGGRAPH_AVAILABLE and GENAI:
                    # Use autonomous LangGraph agent
                    try:
                        initial_state = {
                            "messages": [HumanMessage(content=user_input)],
                            "current_task": "user_request",
                            "files_context": {"files": st.session_state.files},
                            "results": []
                        }
                        
                        result = LANGGRAPH_AGENT.invoke(initial_state)
                        
                        # Extract the final AI response
                        # Priority: 1) Final AIMessage with text content and no tool_calls
                        #           2) Tool results from ToolMessages
                        #           3) AIMessage content even if it also had tool_calls
                        #           4) Fallback to basic Gemini
                        ai_response = None
                        tool_results = []
                        ai_with_tools_content = None
                        
                        for msg in reversed(result["messages"]):
                            # Collect tool results
                            if isinstance(msg, ToolMessage):
                                if msg.content:
                                    tool_results.insert(0, msg.content)
                            # Only consider AIMessage (never HumanMessage)
                            elif isinstance(msg, AIMessage):
                                # Extract text content (handle str or list of parts)
                                text = ""
                                if isinstance(msg.content, str):
                                    text = msg.content.strip()
                                elif isinstance(msg.content, list):
                                    text = " ".join(
                                        p.get("text", "") if isinstance(p, dict) else str(p)
                                        for p in msg.content
                                    ).strip()
                                
                                has_tool_calls = hasattr(msg, 'tool_calls') and msg.tool_calls
                                
                                if text and not has_tool_calls:
                                    # Best case: final AI summary with no tool calls
                                    ai_response = text
                                    break
                                elif text and has_tool_calls and not ai_with_tools_content:
                                    # Backup: AI message that also had tool calls
                                    ai_with_tools_content = text
                        
                        # Build final response with fallback chain
                        if not ai_response:
                            if tool_results:
                                ai_response = "\n\n".join(tool_results)
                            elif ai_with_tools_content:
                                ai_response = ai_with_tools_content
                            else:
                                # Last resort: ask Gemini directly for a summary
                                context = {
                                    "files": st.session_state.files,
                                    "processed_files": st.session_state.preprocessed_files
                                }
                                ai_response = ask_gemini_basic(user_input, context)
                        
                    except Exception as e:
                        st.error(f"Agent error: {str(e)}")
                        ai_response = f"❌ Agent encountered an error: {str(e)}"
                else:
                    # Fallback to basic Gemini
                    context = {
                        "files": st.session_state.files,
                        "processed_files": st.session_state.preprocessed_files
                    }
                    ai_response = ask_gemini_basic(user_input, context)
            
            # Add AI response to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": ai_response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Track chat in session + database (if auth enabled) + AWS
            try:
                st.session_state.session_chat_log.append({
                    "question": user_input,
                    "answer": ai_response[:500],
                    "timestamp": datetime.now().isoformat()
                })
                
                file_context = None
                if st.session_state.files:
                    file_names = [f["metadata"].name for f in st.session_state.files.values()]
                    file_context = ", ".join(file_names[:3])
                
                # Save to AWS DynamoDB
                if AWS_AVAILABLE and dynamo_db and dynamo_db.available:
                    user_id = st.session_state.get("user_id", "anonymous")
                    dynamo_db.save_chat(
                        user_id=user_id,
                        message=user_input,
                        response=ai_response,
                        file_context=file_context
                    )
                    if cw_logger and cw_logger.available:
                        cw_logger.track_chat(user_id)
                
                # Fallback: Save to local DB
                elif AUTH_ENABLED and not USE_COGNITO:
                    save_chat_history(
                        user_id=st.session_state.user_id,
                        message=user_input,
                        response=ai_response,
                        file_context=file_context
                    )
            except Exception:
                pass
            
            # Auto-refresh to show new results
            st.rerun()
        
        # Display chat history
        if st.session_state.chat_history:
            st.markdown("---")
            st.markdown("### 💬 Conversation History")
            
            for message in reversed(st.session_state.chat_history[-6:]):  # Show last 6 messages
                timestamp = datetime.fromisoformat(message["timestamp"]).strftime("%H:%M:%S")
                
                if message["role"] == "user":
                    st.markdown(f"""
                    <div style="background-color: #e3f2fd; padding: 15px; border-radius: 10px; margin: 10px 0;color: #000000;">
                        <strong>👤 You</strong> <small>({timestamp})</small><br>
                        {message["content"]}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background-color: #f3e5f5; padding: 15px; border-radius: 10px; margin: 10px 0;color: #000000;">
                        <strong>🤖 Autonomous Agent</strong> <small>({timestamp})</small><br>
                        {message["content"]}
                    </div>
                    """, unsafe_allow_html=True)
            
            if st.button("🗑️ Clear Chat History"):
                st.session_state.chat_history = []
                st.rerun()

with tab4:
    st.header("📊 Results & Downloads")
    
    # Show processed files with enhanced download options
    if st.session_state.preprocessed_files:
        st.subheader("📁 Processed Datasets")
        
        for name, df in st.session_state.preprocessed_files.items():
            with st.expander(f"📄 {name} ({df.shape[0]:,} × {df.shape[1]})", expanded=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.dataframe(df.head(10), use_container_width=True)
                
                with col2:
                    # Download as CSV
                    csv_buffer = io.BytesIO()
                    df.to_csv(csv_buffer, index=False)
                    csv_buffer.seek(0)
                    
                    st.download_button(
                        "📥 Download CSV",
                        data=csv_buffer.getvalue(),
                        file_name=name,
                        mime="text/csv",
                        key=f"csv_{name}"
                    )
                    
                    # Basic stats
                    st.metric("Rows", f"{df.shape[0]:,}")
                    st.metric("Columns", df.shape[1])
                    
                    # Show data types
                    st.write("**Data Types:**")
                    dtype_info = df.dtypes.value_counts()
                    for dtype, count in dtype_info.items():
                        st.text(f"{dtype}: {count}")
    
    # Show cached plots with better handling
    if st.session_state.plot_cache:
        st.subheader("📈 Generated Visualizations")
        
        for cache_key, plots in st.session_state.plot_cache.items():
            timestamp_str = cache_key.split('_')[-1] if '_' in cache_key else 'unknown'
            try:
                timestamp = datetime.fromtimestamp(int(timestamp_str)).strftime("%H:%M:%S")
            except:
                timestamp = "unknown"
                
            with st.expander(f"📊 Plot Set: {cache_key} (Created: {timestamp})", expanded=True):
                for i, (title, fig) in enumerate(plots):
                    st.markdown(f"**{title}**")
                    
                    try:
                        if hasattr(fig, 'update_layout'):  # Plotly figure
                            st.plotly_chart(fig, use_container_width=True)
                        elif hasattr(fig, 'savefig'):  # Matplotlib figure
                            st.pyplot(fig)
                        else:
                            st.warning(f"Unknown plot type for {title}")
                    except Exception as e:
                        st.error(f"Error displaying {title}: {str(e)}")
                    
                    # Add separator between plots
                    if i < len(plots) - 1:
                        st.markdown("---")
        
        # Clear plots button
        if st.button("🗑️ Clear All Plots"):
            st.session_state.plot_cache = {}
            st.rerun()
    
    # Show processing history
    if st.session_state.processing_history:
        st.subheader("📋 Processing History")
        for history in reversed(st.session_state.processing_history[-10:]):
            timestamp = datetime.fromisoformat(history.timestamp).strftime("%Y-%m-%d %H:%M:%S")
            status_icon = "✅" if history.success else "❌"
            
            st.markdown(f"""
            **{status_icon} {history.action.replace('_', ' ').title()}** _{timestamp}_  
            Result: {history.result_shape[0]:,} × {history.result_shape[1]} | {history.message}
            """)

with tab5:
    st.header("📈 Reports & Export")
    
    if not st.session_state.files:
        st.info("Upload files to generate reports!")
    else:
        st.subheader("📋 Generate Comprehensive Report")
        
        # Report configuration
        report_files = st.multiselect(
            "Select files for report",
            options=list(st.session_state.files.keys()),
            default=list(st.session_state.files.keys()),
            format_func=lambda x: f"File {x}: {st.session_state.files[x]['metadata'].name}"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            include_analysis = st.checkbox("Include Data Analysis", value=True)
            include_plots = st.checkbox("Include Visualizations", value=True)
        with col2:
            include_preprocessing = st.checkbox("Include Processing History", value=True)
            include_recommendations = st.checkbox("Include AI Recommendations", value=True)
        
        if st.button("📊 Generate Report"):
            with st.spinner("Generating comprehensive report..."):
                # Create report content
                report_content = []
                report_content.append("# 📊 EDA Analysis Report")
                report_content.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                report_content.append(f"Total files analyzed: {len(report_files)}")
                report_content.append("\n---\n")
                
                # File summaries
                report_content.append("## 📁 Dataset Overview")
                for file_idx in report_files:
                    file_data = st.session_state.files[file_idx]
                    metadata = file_data["metadata"]
                    df = file_data["df"]
                    
                    report_content.append(f"### File {file_idx}: {metadata.name}")
                    report_content.append(f"- **Shape:** {metadata.shape[0]:,} rows × {metadata.shape[1]} columns")
                    report_content.append(f"- **Size:** {metadata.file_size / 1024**2:.1f} MB")
                    report_content.append(f"- **Data Types:** {len(set(metadata.dtypes.values()))} unique types")
                    
                    if include_analysis:
                        profile = generate_data_profile(df)
                        report_content.append(f"- **Data Quality Score:** {profile['data_quality_score']:.1f}/100")
                        report_content.append(f"- **Missing Values:** {sum(metadata.missing_count.values()):,}")
                        report_content.append(f"- **Duplicate Rows:** {profile['duplicate_rows']:,}")
                    
                    report_content.append("")
                
                # Processing history
                if include_preprocessing and st.session_state.processing_history:
                    report_content.append("## 🛠️ Processing History")
                    for history in st.session_state.processing_history[-10:]:
                        timestamp = datetime.fromisoformat(history.timestamp).strftime("%Y-%m-%d %H:%M:%S")
                        status = "✅ Success" if history.success else "❌ Failed"
                        report_content.append(f"- **{history.action.replace('_', ' ').title()}** ({timestamp}): {status}")
                        report_content.append(f"  - Result: {history.result_shape[0]:,} × {history.result_shape[1]}")
                        report_content.append(f"  - {history.message}")
                    report_content.append("")
                
                # AI Recommendations
                if include_recommendations and GENAI:
                    report_content.append("## 🤖 AI Recommendations")
                    try:
                        context = f"Dataset analysis summary:\n"
                        for file_idx in report_files:
                            metadata = st.session_state.files[file_idx]["metadata"]
                            context += f"- {metadata.name}: {metadata.shape[0]:,} × {metadata.shape[1]}, {sum(metadata.missing_count.values())} missing values\n"
                        
                        prompt = f"""Based on this dataset analysis, provide 5 specific, actionable recommendations for further analysis:

{context}

Format as numbered list with brief explanations."""
                        # Create model instance first
                        model = GENAI.GenerativeModel("gemini-2.5-flash")
                        response = model.generate_content(
                            contents=[{
                                "role": "user",
                                "parts": [{"text": prompt}]
                            }]
                        )
                        if response.candidates and response.candidates[0].content.parts:
                            report_content.append(response.candidates[0].content.parts[0].text)
                        else:
                            report_content.append("No recommendations could be generated at this time.")
                    except Exception as e:
                        report_content.append(f"Could not generate recommendations: {str(e)}")
                    
                    report_content.append("")
                
                # Export options
                report_text = "\n".join(report_content)
                
                # Create downloadable markdown
                st.download_button(
                    "📥 Download Report (Markdown)",
                    data=report_text,
                    file_name=f"eda_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
                
                # Display report preview
                st.markdown("### 📋 Report Preview")
                st.markdown(report_text)
        
        # Bulk export options
        st.subheader("📦 Bulk Export")
        
        if st.session_state.preprocessed_files:
            if st.button("📁 Export All Processed Files"):
                import zipfile
                zip_buffer = io.BytesIO()
                
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for name, df in st.session_state.preprocessed_files.items():
                        csv_data = df.to_csv(index=False)
                        zip_file.writestr(name, csv_data)
                
                zip_buffer.seek(0)
                st.download_button(
                    "📥 Download All as ZIP",
                    data=zip_buffer.getvalue(),
                    file_name=f"processed_datasets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip"
                )

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>🤖 <strong>Autonomous EDA Agent</strong> | Powered by LangGraph & Gemini AI</p>
    <p><small>Upload • Chat • Execute • Download</small></p>
</div>
""", unsafe_allow_html=True)

# Sidebar footer with system info
if st.session_state.files:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 System Status")
    st.sidebar.markdown(f"🔧 LangGraph: {'✅ Available' if LANGGRAPH_AVAILABLE else '❌ Not Available'}")
    st.sidebar.markdown(f"🤖 Gemini: {'✅ Connected' if GENAI else '❌ Not Connected'}")
    st.sidebar.markdown(f"📁 Files Loaded: {len(st.session_state.files)}")
    st.sidebar.markdown(f"🛠️ Processed: {len(st.session_state.preprocessed_files)}")
    st.sidebar.markdown(f"📊 Plots Cached: {len(st.session_state.plot_cache)}")
    st.sidebar.markdown(f"💬 Chat Messages: {len(st.session_state.chat_history)}")

# Performance monitoring
if len(st.session_state.files) > 0:
    total_memory = sum(file_data["metadata"].file_size for file_data in st.session_state.files.values())
    if total_memory > 100 * 1024 * 1024:  # 100MB
        st.sidebar.warning(f"⚠️ Large dataset detected ({total_memory / 1024**2:.1f} MB). Consider processing in smaller chunks.")

# Keyboard shortcuts and tips
st.sidebar.markdown("""
---
### ⌨️ Agent Commands
- **"analyze file 0"** - Get insights
- **"fill missing with mean"** - Handle missing data
- **"do outlier analysis and min max scaling"** - Preprocess
- **"create plots for file 1"** - Generate visualizations
- **"merge files 0 and 1"** - Combine datasets
""")

# Quick actions in sidebar
if st.session_state.files and st.session_state.last_idx is not None:
    st.sidebar.markdown("### ⚡ Quick Actions")
    
    if st.sidebar.button("🧹 Clean Latest File"):
        with st.spinner("Processing..."):
            df, name, idx = get_file_by_ref(st.session_state.last_idx)
            params = {
                "handle_missing": True,
                "missing_strategy": "mean",
                "handle_outliers": True,
                "outlier_action": "cap"
            }
            processed_df, actions = enhanced_preprocessing(df, params)
            processed_name = f"quick_clean_{name.split('.')[0]}_{int(time.time())}.csv"
            st.session_state.preprocessed_files[processed_name] = processed_df
            st.sidebar.success("✅ Cleaned!")
    
    if st.sidebar.button("📊 Visualize Latest"):
        with st.spinner("Creating plots..."):
            df, name, idx = get_file_by_ref(st.session_state.last_idx)
            plots = create_smart_visualizations(df, max_plots=4)
            if plots:
                cache_key = f"sidebar_viz_{int(time.time())}"
                st.session_state.plot_cache[cache_key] = plots
                st.sidebar.success("✅ Plots created!")

# AWS Status Panel
if AWS_AVAILABLE and aws_config:
    with st.sidebar.expander("☁️ AWS Services", expanded=False):
        status = aws_config.get_status()
        st.markdown(f"**Region:** `{status['region']}`")
        service_icons = {
            'dynamodb': ('🗄️ DynamoDB', status.get('dynamodb', False)),
            'cognito': ('🔐 Cognito', status.get('cognito', False)),
            'cloudwatch': ('📊 CloudWatch', status.get('cloudwatch', False)),
            'ssm': ('🔑 SSM', status.get('ssm', False)),
            'sqs': ('📨 SQS', status.get('sqs', False)),
            'lambda': ('⚡ Lambda', status.get('lambda', False)),
            's3': ('📦 S3', status.get('s3', False)),
        }
        for key, (label, enabled) in service_icons.items():
            icon = "✅" if enabled else "⬜"
            st.markdown(f"{icon} {label}")
        
        # Show SQS queue stats if available
        if sqs_client and sqs_client.available:
            stats = sqs_client.get_queue_stats()
            if stats:
                st.markdown(f"**Queue:** {stats.get('pending', 0)} pending, {stats.get('in_flight', 0)} processing")

# Debug panel (only show if in development)
if st.sidebar.checkbox("🔧 Debug Mode", value=False):
    st.sidebar.markdown("### 🔍 Debug Info")
    with st.sidebar.expander("Session State"):
        st.write("Files:", list(st.session_state.files.keys()))
        st.write("Processed:", list(st.session_state.preprocessed_files.keys()))
        st.write("Plot Cache:", list(st.session_state.plot_cache.keys()))
        st.write("Last Index:", st.session_state.last_idx)
        if AWS_AVAILABLE:
            st.write("AWS Region:", aws_config.region if aws_config else "N/A")
            st.write("DynamoDB:", dynamo_db.available if dynamo_db else False)
            st.write("Cognito:", cognito_auth.available if cognito_auth else False)
            st.write("S3:", s3_storage.available if s3_storage else False)

# Auto-refresh option
if st.sidebar.button("🔄 Refresh App"):
    st.rerun()

# Error handling wrapper for the entire app
try:
    # Main app logic is above
    pass
except Exception as e:
    st.error("🚨 Application Error")
    st.exception(e)
    
    if st.button("🔄 Reset Application"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Add some custom styling for better UX
st.markdown("""
<style>
.stButton > button {
    border-radius: 20px;
    border: none;
    padding: 0.5rem 1rem;
    font-weight: 600;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

.stSelectbox > div > div {
    border-radius: 10px;
}

.stTextArea > div > div {
    border-radius: 10px;
}

div[data-testid="metric-container"] {
    background-color: #f0f2f6;
    border: 1px solid #e0e4e8;
    padding: 1rem;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# Success message for new users
if not st.session_state.files and not st.session_state.get('welcome_shown', False):
    st.success("🎉 Welcome to the Autonomous EDA Agent! Upload your CSV/Excel files and start chatting with the AI to get instant data analysis results.")
    st.session_state.welcome_shown = True