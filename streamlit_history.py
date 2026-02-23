"""
User History Viewer Component
Shows user's chat history, uploaded files, and analyses
"""

import streamlit as st
from datetime import datetime
from streamlit_auth import get_user_chat_history, get_user_files
import pandas as pd


def format_timestamp(timestamp):
    """Format timestamp for display"""
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except:
            return timestamp
    
    now = datetime.now()
    diff = now - timestamp
    
    if diff.days == 0:
        if diff.seconds < 60:
            return "Just now"
        elif diff.seconds < 3600:
            mins = diff.seconds // 60
            return f"{mins} minute{'s' if mins != 1 else ''} ago"
        else:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.days == 1:
        return "Yesterday"
    elif diff.days < 7:
        return f"{diff.days} days ago"
    else:
        return timestamp.strftime("%b %d, %Y")


def show_chat_history():
    """Display user's chat history"""
    st.subheader("💬 Chat History")
    
    if "user_id" not in st.session_state:
        st.warning("Please login to view history")
        return
    
    # Get chat history from database
    chats = get_user_chat_history(st.session_state.user_id, limit=100)
    
    if not chats:
        st.info("📭 No chat history yet. Start a conversation to see it here!")
        return
    
    # Display count
    st.caption(f"Showing {len(chats)} conversation{'s' if len(chats) != 1 else ''}")
    
    # Search/filter
    search = st.text_input("🔍 Search conversations", placeholder="Type to search...")
    
    # Filter chats
    filtered_chats = chats
    if search:
        search_lower = search.lower()
        filtered_chats = [
            chat for chat in chats 
            if search_lower in chat.message.lower() or search_lower in (chat.response or "").lower()
        ]
    
    if not filtered_chats:
        st.warning(f"No results found for '{search}'")
        return
    
    # Display chats
    for idx, chat in enumerate(reversed(filtered_chats)):
        with st.expander(
            f"💭 {chat.message[:80]}{'...' if len(chat.message) > 80 else ''} • {format_timestamp(chat.timestamp)}"
        ):
            col1, col2 = st.columns([1, 5])
            
            with col1:
                st.markdown("**👤 You:**")
            with col2:
                st.markdown(f"{chat.message}")
            
            st.markdown("---")
            
            col1, col2 = st.columns([1, 5])
            with col1:
                st.markdown("**🤖 AI:**")
            with col2:
                st.markdown(f"{chat.response or 'No response'}")
            
            # Show metadata
            st.caption(f"🕐 {chat.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            if chat.file_context:
                st.caption(f"📁 Context: {chat.file_context}")


def show_files_history():
    """Display user's uploaded files"""
    st.subheader("📁 Uploaded Files")
    
    if "user_id" not in st.session_state:
        st.warning("Please login to view history")
        return
    
    # Get files from database
    files = get_user_files(st.session_state.user_id)
    
    if not files:
        st.info("📭 No files uploaded yet. Upload a CSV to see it here!")
        return
    
    # Display count
    st.caption(f"Total files: {len(files)}")
    
    # Create DataFrame for display
    files_data = []
    for file in files:
        files_data.append({
            "Filename": file.filename,
            "Rows": f"{file.rows:,}" if file.rows else "N/A",
            "Columns": f"{file.columns:,}" if file.columns else "N/A",
            "Size": f"{file.file_size / 1024:.1f} KB" if file.file_size else "N/A",
            "Uploaded": format_timestamp(file.upload_time)
        })
    
    if files_data:
        df = pd.DataFrame(files_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Detailed view
    st.markdown("---")
    st.markdown("**📊 Detailed View**")
    
    for file in reversed(files):
        with st.expander(f"📄 {file.filename} • {format_timestamp(file.upload_time)}"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Rows", f"{file.rows:,}" if file.rows else "N/A")
            with col2:
                st.metric("Columns", f"{file.columns:,}" if file.columns else "N/A")
            with col3:
                st.metric("Size", f"{file.file_size / 1024:.1f} KB" if file.file_size else "N/A")
            with col4:
                st.metric("File ID", file.file_id[:8] + "...")
            
            st.caption(f"📅 Uploaded: {file.upload_time.strftime('%Y-%m-%d %H:%M:%S')}")
            st.caption(f"📂 Path: {file.file_path}")


def show_user_history():
    """Main history display function"""
    
    # Custom CSS for history page - Dark Theme
    st.markdown("""
    <style>
        .history-header {
            background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 50%, #EC4899 100%);
            padding: 2rem;
            border-radius: 12px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 8px 24px rgba(139, 92, 246, 0.4);
        }
        .history-header h1 {
            margin: 0;
            font-size: 2rem;
            font-weight: 700;
        }
        .stat-card {
            background: #1E1E2E;
            border-left: 4px solid #8B5CF6;
            padding: 1.2rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            color: #FAFAFA;
        }
        /* Expander styling */
        .streamlit-expanderHeader {
            background: #1E1E2E;
            border-radius: 8px;
        }
        /* Metric styling */
        div[data-testid="stMetricValue"] {
            color: #8B5CF6;
            font-weight: 600;
        }
        div[data-testid="stMetricLabel"] {
            color: #A1A1AA;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="history-header">
        <h1>📚 Your History</h1>
        <p style="margin: 0; opacity: 0.9;">View your past conversations and uploaded files</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check authentication
    if "user_id" not in st.session_state:
        st.warning("⚠️ Please login to view your history")
        return
    
    # User info
    st.markdown(f"""
    <div class="stat-card">
        <strong>👤 Logged in as:</strong> {st.session_state.get('name', 'User')} 
        (@{st.session_state.get('username', '')})
    </div>
    """, unsafe_allow_html=True)
    
    # Statistics
    chats = get_user_chat_history(st.session_state.user_id, limit=1000)
    files = get_user_files(st.session_state.user_id)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💬 Total Chats", len(chats))
    with col2:
        st.metric("📁 Files Uploaded", len(files))
    with col3:
        total_rows = sum(f.rows for f in files if f.rows)
        st.metric("📊 Total Rows Analyzed", f"{total_rows:,}")
    
    st.markdown("---")
    
    # Tabs for different history types
    tab1, tab2 = st.tabs(["💬 Chat History", "📁 Files"])
    
    with tab1:
        show_chat_history()
    
    with tab2:
        show_files_history()
    
    # Export options
    st.markdown("---")
    st.subheader("📥 Export History")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export Chat History (CSV)", use_container_width=True):
            if chats:
                chat_data = [{
                    "Timestamp": chat.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    "Your Message": chat.message,
                    "AI Response": chat.response,
                    "File Context": chat.file_context or ""
                } for chat in chats]
                
                df = pd.DataFrame(chat_data)
                csv = df.to_csv(index=False)
                
                st.download_button(
                    "⬇️ Download Chat History",
                    csv,
                    file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No chat history to export")
    
    with col2:
        if st.button("📥 Export Files List (CSV)", use_container_width=True):
            if files:
                files_data = [{
                    "Filename": f.filename,
                    "Rows": f.rows or 0,
                    "Columns": f.columns or 0,
                    "Size (KB)": f"{f.file_size / 1024:.2f}" if f.file_size else "0",
                    "Upload Time": f.upload_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "File ID": f.file_id
                } for f in files]
                
                df = pd.DataFrame(files_data)
                csv = df.to_csv(index=False)
                
                st.download_button(
                    "⬇️ Download Files List",
                    csv,
                    file_name=f"files_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No files to export")
