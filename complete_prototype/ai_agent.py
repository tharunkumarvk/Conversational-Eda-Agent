"""
AI Agent Module
Handles Gemini AI integration and LangGraph agent for EDA tasks
"""

import os
import streamlit as st
from typing import Dict, Any

# Gemini imports
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except:
    GENAI_AVAILABLE = False
    genai = None

# LangGraph imports
try:
    from langgraph.graph import StateGraph, END
    from langchain_core.messages import HumanMessage, AIMessage
    from langchain_google_genai import ChatGoogleGenerativeAI
    LANGGRAPH_AVAILABLE = True
except:
    LANGGRAPH_AVAILABLE = False


def get_api_key() -> str:
    """Get API key from environment or secrets"""
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        try:
            if hasattr(st, "secrets"):
                secrets_dict = dict(st.secrets)
                key = secrets_dict.get("GOOGLE_API_KEY")
        except:
            pass
    return key


def init_gemini():
    """Initialize Gemini AI"""
    if not GENAI_AVAILABLE:
        return None
    
    key = get_api_key()
    if not key:
        st.error("GOOGLE_API_KEY not found!")
        return None
    
    try:
        genai.configure(api_key=key)
        list(genai.list_models())  # Test connection
        return genai
    except Exception as e:
        st.error(f"Gemini initialization error: {e}")
        return None


def ask_gemini(prompt: str, context: Dict[str, Any] = None) -> str:
    """Ask Gemini AI with context"""
    gemini = init_gemini()
    if not gemini:
        return "❌ Gemini not available - check your API key"
    
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        # Build context
        context_str = ""
        if context and "files" in context:
            context_str = "\nAvailable datasets:\n"
            for idx, file_data in context["files"].items():
                metadata = file_data["metadata"]
                context_str += f"- File {idx}: {metadata.name} ({metadata.shape[0]}x{metadata.shape[1]})\n"
                context_str += f"  Columns: {', '.join(metadata.columns[:5])}{'...' if len(metadata.columns) > 5 else ''}\n"
        
        full_prompt = f"""You are an expert EDA (Exploratory Data Analysis) assistant. Help users analyze their datasets.

{context_str}

User request: {prompt}

Provide actionable insights and specific recommendations. Be concise and helpful."""
        
        response = model.generate_content(contents=[{"role": "user", "parts": [{"text": full_prompt}]}])
        
        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        return "No response generated"
    
    except Exception as e:
        return f"❌ Error: {str(e)}"


def generate_analysis_insights(df_summary: Dict[str, Any]) -> str:
    """Generate AI insights about dataset"""
    gemini = init_gemini()
    if not gemini:
        return "AI insights unavailable"
    
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        prompt = f"""Analyze this dataset and provide 5 key insights:

Dataset Shape: {df_summary['shape'][0]} rows × {df_summary['shape'][1]} columns
Missing Values: {sum(df_summary['missing'].values())} total missing values
Duplicates: {df_summary['duplicates']} duplicate rows

Provide:
1. Data quality assessment
2. Notable patterns or issues
3. Recommendations for preprocessing
4. Suggested analyses to perform
5. Potential use cases

Be specific and actionable."""
        
        response = model.generate_content(contents=[{"role": "user", "parts": [{"text": prompt}]}])
        
        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        return "Could not generate insights"
    
    except Exception as e:
        return f"Error generating insights: {e}"


def suggest_visualizations(columns: list, dtypes: Dict[str, str]) -> str:
    """Suggest appropriate visualizations"""
    gemini = init_gemini()
    if not gemini:
        return "Visualization suggestions unavailable"
    
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        numeric_cols = [col for col, dtype in dtypes.items() if 'int' in str(dtype) or 'float' in str(dtype)]
        categorical_cols = [col for col, dtype in dtypes.items() if 'object' in str(dtype)]
        
        prompt = f"""Suggest the best visualizations for this dataset:

Numeric columns ({len(numeric_cols)}): {', '.join(numeric_cols[:5])}
Categorical columns ({len(categorical_cols)}): {', '.join(categorical_cols[:5])}

Provide 5 specific visualization recommendations with:
1. Chart type
2. Which columns to use
3. What insight it will reveal

Be specific about column combinations."""
        
        response = model.generate_content(contents=[{"role": "user", "parts": [{"text": prompt}]}])
        
        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        return "Could not generate suggestions"
    
    except Exception as e:
        return f"Error: {e}"


def explain_preprocessing_step(step: str, before_shape: tuple, after_shape: tuple) -> str:
    """Explain what a preprocessing step did"""
    gemini = init_gemini()
    if not gemini:
        return f"Applied {step}: {before_shape} → {after_shape}"
    
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        prompt = f"""Briefly explain what happened in this preprocessing step:

Step: {step}
Before: {before_shape[0]} rows × {before_shape[1]} columns
After: {after_shape[0]} rows × {after_shape[1]} columns

In 2-3 sentences, explain the change and its impact."""
        
        response = model.generate_content(contents=[{"role": "user", "parts": [{"text": prompt}]}])
        
        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        return f"{step}: {before_shape} → {after_shape}"
    
    except:
        return f"{step}: Shape changed from {before_shape} to {after_shape}"
