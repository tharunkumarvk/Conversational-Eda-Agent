"""
User History Module
Displays user's chat history and uploaded files
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from auth import get_user_chat_history, get_user_files


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
            return f"{diff.seconds // 60}m ago"
        else:
            return f"{diff.seconds // 3600}h ago"
    elif diff.days == 1:
        return "Yesterday"
    elif diff.days < 7:
        return f"{diff.days}d ago"
    else:
        return timestamp.strftime("%b %d, %Y")


def show_chat_history():
    """Display user's chat history"""
    st.subheader("💬 Chat History")
    
    if "user_id" not in st.session_state:
        st.warning("Please login to view history")
        return
    
    chats = get_user_chat_history(st.session_state.user_id, limit=100)
    
    if not chats:
        st.info("📭 No chat history yet. Start a conversation!")
        return
    
    st.caption(f"Showing {len(chats)} conversation(s)")
    search = st.text_input("🔍 Search conversations", placeholder="Type to search...")
    
    filtered_chats = chats
    if search:
        search_lower = search.lower()
        filtered_chats = [c for c in chats if search_lower in c.message.lower() or search_lower in (c.response or "").lower()]
    
    if not filtered_chats:
        st.warning(f"No results for '{search}'")
        return
    
    for chat in reversed(filtered_chats):
        with st.expander(f"💭 {chat.message[:80]}{'...' if len(chat.message) > 80 else ''} • {format_timestamp(chat.timestamp)}"):
            st.markdown(f"**👤 You:** {chat.message}")
            st.markdown("---")
            st.markdown(f"**🤖 AI:** {chat.response or 'No response'}")
            st.caption(f"🕐 {chat.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            if chat.file_context:
                st.caption(f"📁 {chat.file_context}")


def show_files_history():
    """Display user's uploaded files"""
    st.subheader("📁 Uploaded Files")
    
    if "user_id" not in st.session_state:
        st.warning("Please login to view history")
        return
    
    files = get_user_files(st.session_state.user_id)
    
    if not files:
        st.info("📭 No files uploaded yet")
        return
    
    st.caption(f"Total files: {len(files)}")
    
    files_data = [{
        "Filename": f.filename,
        "Rows": f"{f.rows:,}" if f.rows else "N/A",
        "Columns": f"{f.columns:,}" if f.columns else "N/A",
        "Size": f"{f.file_size / 1024:.1f} KB" if f.file_size else "N/A",
        "Uploaded": format_timestamp(f.upload_time)
    } for f in files]
    
    if files_data:
        st.dataframe(pd.DataFrame(files_data), use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("**📊 Detailed View**")
    
    for file in reversed(files):
        with st.expander(f"📄 {file.filename} • {format_timestamp(file.upload_time)}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rows", f"{file.rows:,}" if file.rows else "N/A")
            with col2:
                st.metric("Columns", f"{file.columns:,}" if file.columns else "N/A")
            with col3:
                st.metric("Size", f"{file.file_size / 1024:.1f} KB" if file.file_size else "N/A")
            
            st.caption(f"📅 {file.upload_time.strftime('%Y-%m-%d %H:%M:%S')}")


def show_user_history():
    """Main history display"""
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
        .stat-card {
            background: #1E1E2E;
            border-left: 4px solid #8B5CF6;
            padding: 1.2rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="history-header">
        <h1>📚 Your History</h1>
        <p style="margin: 0; opacity: 0.9;">View past conversations and files</p>
    </div>
    """, unsafe_allow_html=True)
    
    if "user_id" not in st.session_state:
        st.warning("⚠️ Please login to view history")
        return
    
    st.markdown(f"""
    <div class="stat-card">
        <strong>👤 Logged in as:</strong> {st.session_state.get('name', 'User')} 
        (@{st.session_state.get('username', '')})
    </div>
    """, unsafe_allow_html=True)
    
    chats = get_user_chat_history(st.session_state.user_id, limit=1000)
    files = get_user_files(st.session_state.user_id)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💬 Total Chats", len(chats))
    with col2:
        st.metric("📁 Files Uploaded", len(files))
    with col3:
        total_rows = sum(f.rows for f in files if f.rows)
        st.metric("📊 Total Rows", f"{total_rows:,}")
    
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["💬 Chat History", "📁 Files"])
    
    with tab1:
        show_chat_history()
    
    with tab2:
        show_files_history()
    
    st.markdown("---")
    st.subheader("📥 Export History")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export Chats (CSV)", use_container_width=True):
            if chats:
                chat_data = [{
                    "Timestamp": c.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    "Message": c.message,
                    "Response": c.response,
                    "Context": c.file_context or ""
                } for c in chats]
                
                csv = pd.DataFrame(chat_data).to_csv(index=False)
                st.download_button("⬇️ Download", csv, 
                                 file_name=f"chat_history_{datetime.now().strftime('%Y%m%d')}.csv",
                                 mime="text/csv")
            else:
                st.info("No chats to export")
    
    with col2:
        if st.button("📥 Export Files (CSV)", use_container_width=True):
            if files:
                files_data = [{
                    "Filename": f.filename,
                    "Rows": f.rows or 0,
                    "Columns": f.columns or 0,
                    "Size_KB": f"{f.file_size / 1024:.2f}" if f.file_size else "0",
                    "Upload_Time": f.upload_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "File_ID": f.file_id
                } for f in files]
                
                csv = pd.DataFrame(files_data).to_csv(index=False)
                st.download_button("⬇️ Download", csv,
                                 file_name=f"files_history_{datetime.now().strftime('%Y%m%d')}.csv",
                                 mime="text/csv")
            else:
                st.info("No files to export")
