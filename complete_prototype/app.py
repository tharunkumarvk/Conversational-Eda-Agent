"""
Minimal EDA Tool - Complete Prototype
Main Streamlit Application
"""

import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import os

# Import custom modules
from auth import check_authentication, show_logout_button, save_user_file, save_chat_history
from data_utils import (
    load_file, create_metadata, get_column_info,
    handle_missing_values, handle_outliers, scale_features, encode_categorical,
    merge_datasets, get_data_summary, detect_data_quality_issues
)
from ai_agent import init_gemini, ask_gemini, generate_analysis_insights, suggest_visualizations, explain_preprocessing_step
from visualizations import (
    create_distribution_plot, create_correlation_heatmap, create_scatter_plot,
    create_box_plot, create_line_plot, create_pie_chart, create_bar_chart,
    create_3d_scatter, create_missing_data_plot, create_summary_stats_table
)
from user_history import show_user_history


# Page config
st.set_page_config(
    page_title="Minimal EDA Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 50%, #EC4899 100%);
        padding: 2.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(139, 92, 246, 0.5);
    }
    .metric-card {
        background: #1E1E2E;
        border-left: 4px solid #8B5CF6;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    .chat-message {
        background: #1E1E2E;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 3px solid #8B5CF6;
    }
    .ai-message {
        border-left-color: #EC4899;
    }
    .stButton > button {
        background: linear-gradient(135deg, #8B5CF6, #6366F1);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        box-shadow: 0 6px 20px rgba(139, 92, 246, 0.6);
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if "current_df" not in st.session_state:
        st.session_state.current_df = None
    if "file_metadata" not in st.session_state:
        st.session_state.file_metadata = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "page" not in st.session_state:
        st.session_state.page = "main"


def show_header():
    """Display app header"""
    st.markdown("""
    <div class="main-header">
        <h1>📊 Minimal EDA Tool</h1>
        <p style="font-size: 1.1rem; margin: 0;">AI-Powered Data Analysis Platform</p>
    </div>
    """, unsafe_allow_html=True)


def handle_file_upload():
    """Handle file upload and processing"""
    st.subheader("📁 Upload Dataset")
    
    uploaded_file = st.file_uploader(
        "Upload your dataset (CSV, Excel, or JSON)",
        type=["csv", "xlsx", "xls", "json"],
        help="Upload a file to start your analysis"
    )
    
    if uploaded_file:
        with st.spinner("🔄 Loading file..."):
            try:
                df = load_file(uploaded_file)
                st.session_state.current_df = df
                st.session_state.file_metadata = create_metadata(df, uploaded_file.name)
                
                # Save to database
                if "user_id" in st.session_state:
                    save_user_file(
                        st.session_state.user_id,
                        uploaded_file.name,
                        df.shape[0],
                        df.shape[1],
                        uploaded_file.size
                    )
                
                st.success(f"✅ Loaded {uploaded_file.name}")
                
                # Show quick preview
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📊 Rows", f"{df.shape[0]:,}")
                with col2:
                    st.metric("📋 Columns", f"{df.shape[1]:,}")
                with col3:
                    st.metric("💾 Size", f"{uploaded_file.size / 1024:.1f} KB")
                
                with st.expander("👀 Preview Data"):
                    st.dataframe(df.head(10), use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ Error loading file: {str(e)}")


def show_overview_tab():
    """Display dataset overview"""
    if st.session_state.current_df is None:
        st.info("📤 Upload a file to see overview")
        return
    
    df = st.session_state.current_df
    
    st.subheader("📊 Dataset Overview")
    
    # Summary statistics
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**📈 Statistical Summary**")
        st.dataframe(df.describe(), use_container_width=True)
    
    with col2:
        st.markdown("**📋 Column Information**")
        col_info = get_column_info(df)
        st.dataframe(col_info, use_container_width=True)
    
    # Data quality
    st.markdown("---")
    st.markdown("**🔍 Data Quality Check**")
    issues = detect_data_quality_issues(df)
    
    if issues:
        for issue in issues:
            st.warning(issue)
    else:
        st.success("✅ No major data quality issues detected!")
    
    # Missing data visualization
    missing_pct = (df.isnull().sum() / len(df)) * 100
    if missing_pct.sum() > 0:
        st.markdown("**🕳️ Missing Data Pattern**")
        fig = create_missing_data_plot(df)
        st.plotly_chart(fig, use_container_width=True)


def show_preprocessing_tab():
    """Data preprocessing interface"""
    if st.session_state.current_df is None:
        st.info("📤 Upload a file to preprocess")
        return
    
    df = st.session_state.current_df
    
    st.subheader("🔧 Data Preprocessing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🕳️ Handle Missing Values**")
        if df.isnull().sum().sum() > 0:
            missing_strategy = st.selectbox(
                "Strategy",
                ["drop", "mean", "median", "mode", "forward_fill", "backward_fill"]
            )
            if st.button("Apply Missing Value Strategy"):
                before_shape = df.shape
                df_clean = handle_missing_values(df, missing_strategy)
                st.session_state.current_df = df_clean
                after_shape = df_clean.shape
                
                st.success(f"✅ Applied {missing_strategy} strategy")
                explanation = explain_preprocessing_step(f"Missing values ({missing_strategy})", before_shape, after_shape)
                st.info(explanation)
        else:
            st.success("✅ No missing values!")
    
    with col2:
        st.markdown("**📊 Handle Outliers**")
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            col_for_outlier = st.selectbox("Column", numeric_cols)
            outlier_method = st.selectbox("Method", ["iqr", "zscore"])
            if st.button("Remove Outliers"):
                before_shape = df.shape
                df_clean = handle_outliers(df, col_for_outlier, outlier_method)
                st.session_state.current_df = df_clean
                after_shape = df_clean.shape
                
                st.success(f"✅ Removed outliers from {col_for_outlier}")
                explanation = explain_preprocessing_step(f"Outlier removal ({outlier_method})", before_shape, after_shape)
                st.info(explanation)
    
    st.markdown("---")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("**🔢 Encode Categorical**")
        cat_cols = df.select_dtypes(include=['object']).columns.tolist()
        if cat_cols:
            col_to_encode = st.selectbox("Column to encode", cat_cols)
            encoding_method = st.selectbox("Method", ["label", "onehot"])
            if st.button("Encode Column"):
                df_encoded = encode_categorical(df, col_to_encode, encoding_method)
                st.session_state.current_df = df_encoded
                st.success(f"✅ Encoded {col_to_encode}")
        else:
            st.info("No categorical columns")
    
    with col4:
        st.markdown("**⚖️ Scale Features**")
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            cols_to_scale = st.multiselect("Columns to scale", numeric_cols)
            scale_method = st.selectbox("Scaling method", ["standard", "minmax", "robust"])
            if cols_to_scale and st.button("Scale Features"):
                df_scaled = scale_features(df, cols_to_scale, scale_method)
                st.session_state.current_df = df_scaled
                st.success(f"✅ Scaled {len(cols_to_scale)} column(s)")


def show_visualization_tab():
    """Visualization interface"""
    if st.session_state.current_df is None:
        st.info("📤 Upload a file to visualize")
        return
    
    df = st.session_state.current_df
    
    st.subheader("📊 Visualizations")
    
    viz_type = st.selectbox(
        "Choose visualization",
        ["Distribution", "Correlation Heatmap", "Scatter Plot", "Box Plot", 
         "Line Plot", "Pie Chart", "Bar Chart", "3D Scatter"]
    )
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=['object']).columns.tolist()
    all_cols = df.columns.tolist()
    
    if viz_type == "Distribution":
        col = st.selectbox("Select column", numeric_cols)
        if col:
            fig = create_distribution_plot(df, col)
            st.plotly_chart(fig, use_container_width=True)
    
    elif viz_type == "Correlation Heatmap":
        if len(numeric_cols) >= 2:
            fig = create_correlation_heatmap(df)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Need at least 2 numeric columns")
    
    elif viz_type == "Scatter Plot":
        col1, col2 = st.columns(2)
        with col1:
            x_col = st.selectbox("X-axis", numeric_cols)
        with col2:
            y_col = st.selectbox("Y-axis", numeric_cols)
        color_col = st.selectbox("Color by (optional)", ["None"] + all_cols)
        
        if x_col and y_col:
            fig = create_scatter_plot(df, x_col, y_col, color_col if color_col != "None" else None)
            st.plotly_chart(fig, use_container_width=True)
    
    elif viz_type == "Box Plot":
        col = st.selectbox("Select column", numeric_cols)
        group_col = st.selectbox("Group by (optional)", ["None"] + cat_cols)
        if col:
            fig = create_box_plot(df, col, group_col if group_col != "None" else None)
            st.plotly_chart(fig, use_container_width=True)
    
    elif viz_type == "Line Plot":
        col1, col2 = st.columns(2)
        with col1:
            x_col = st.selectbox("X-axis", all_cols)
        with col2:
            y_cols = st.multiselect("Y-axis", numeric_cols)
        if x_col and y_cols:
            fig = create_line_plot(df, x_col, y_cols)
            st.plotly_chart(fig, use_container_width=True)
    
    elif viz_type == "Pie Chart":
        col = st.selectbox("Select column", cat_cols + numeric_cols)
        if col:
            fig = create_pie_chart(df, col)
            st.plotly_chart(fig, use_container_width=True)
    
    elif viz_type == "Bar Chart":
        col1, col2 = st.columns(2)
        with col1:
            x_col = st.selectbox("X-axis", all_cols)
        with col2:
            y_col = st.selectbox("Y-axis", numeric_cols)
        if x_col and y_col:
            fig = create_bar_chart(df, x_col, y_col)
            st.plotly_chart(fig, use_container_width=True)
    
    elif viz_type == "3D Scatter":
        if len(numeric_cols) >= 3:
            col1, col2, col3 = st.columns(3)
            with col1:
                x_col = st.selectbox("X-axis", numeric_cols)
            with col2:
                y_col = st.selectbox("Y-axis", numeric_cols)
            with col3:
                z_col = st.selectbox("Z-axis", numeric_cols)
            
            color_col = st.selectbox("Color by (optional)", ["None"] + all_cols)
            
            if x_col and y_col and z_col:
                fig = create_3d_scatter(df, x_col, y_col, z_col, color_col if color_col != "None" else None)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Need at least 3 numeric columns for 3D scatter")


def show_ai_chat_tab():
    """AI chat interface"""
    st.subheader("🤖 AI Assistant")
    
    # Initialize Gemini
    if "gemini_initialized" not in st.session_state:
        init_gemini()
        st.session_state.gemini_initialized = True
    
    # Auto-generate insights
    if st.session_state.current_df is not None and st.button("✨ Generate Insights"):
        with st.spinner("🤔 Analyzing data..."):
            df_summary = get_data_summary(st.session_state.current_df)
            insights = generate_analysis_insights(df_summary)
            st.markdown(f"<div class='chat-message ai-message'>{insights}</div>", unsafe_allow_html=True)
    
    # Suggest visualizations
    if st.session_state.current_df is not None and st.button("📊 Suggest Visualizations"):
        with st.spinner("🎨 Thinking..."):
            cols = st.session_state.current_df.columns.tolist()
            dtypes = st.session_state.current_df.dtypes.to_dict()
            suggestions = suggest_visualizations(cols, dtypes)
            st.markdown(f"<div class='chat-message ai-message'>{suggestions}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("**💬 Ask Questions**")
    
    # Chat interface
    for msg in st.session_state.chat_history:
        st.markdown(f"<div class='chat-message'>👤 You: {msg['user']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='chat-message ai-message'>🤖 AI: {msg['ai']}</div>", unsafe_allow_html=True)
    
    user_question = st.text_input("Ask about your data...", placeholder="e.g., What correlations exist in my data?")
    
    if st.button("Send") and user_question:
        context = ""
        if st.session_state.current_df is not None:
            context = get_data_summary(st.session_state.current_df)
        
        with st.spinner("🤔 Thinking..."):
            response = ask_gemini(user_question, context)
            
            st.session_state.chat_history.append({
                "user": user_question,
                "ai": response
            })
            
            # Save to database
            if "user_id" in st.session_state:
                file_context = st.session_state.file_metadata.filename if st.session_state.file_metadata else None
                save_chat_history(st.session_state.user_id, user_question, response, file_context)
            
            st.rerun()


def show_export_tab():
    """Data export interface"""
    if st.session_state.current_df is None:
        st.info("📤 Upload and process a file to export")
        return
    
    st.subheader("📥 Export Data")
    
    df = st.session_state.current_df
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📄 Export as CSV**")
        csv = df.to_csv(index=False)
        st.download_button(
            "⬇️ Download CSV",
            csv,
            file_name=f"processed_data_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        st.markdown("**📊 Export as Excel**")
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
        
        st.download_button(
            "⬇️ Download Excel",
            buffer.getvalue(),
            file_name=f"processed_data_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    st.markdown("---")
    st.markdown(f"**Current dataset:** {df.shape[0]:,} rows × {df.shape[1]:,} columns")


def main():
    """Main application"""
    initialize_session_state()
    
    # Check authentication
    if not check_authentication():
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div style="background: #1E1E2E; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
            <h3 style="color: #8B5CF6; margin: 0;">👤 {st.session_state.get('name', 'User')}</h3>
            <p style="margin: 0; color: #9CA3AF;">@{st.session_state.get('username', '')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        show_logout_button()
        
        st.markdown("---")
        
        # Navigation
        page = st.radio("🧭 Navigate", ["📊 Main App", "📚 History"], label_visibility="collapsed")
        
        if page == "📚 History":
            st.session_state.page = "history"
        else:
            st.session_state.page = "main"
    
    # Route to appropriate page
    if st.session_state.page == "history":
        show_user_history()
        return
    
    # Main app
    show_header()
    
    handle_file_upload()
    
    if st.session_state.current_df is not None:
        st.markdown("---")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview", 
            "🔧 Preprocessing", 
            "📈 Visualizations", 
            "🤖 AI Assistant", 
            "📥 Export"
        ])
        
        with tab1:
            show_overview_tab()
        
        with tab2:
            show_preprocessing_tab()
        
        with tab3:
            show_visualization_tab()
        
        with tab4:
            show_ai_chat_tab()
        
        with tab5:
            show_export_tab()


if __name__ == "__main__":
    main()
