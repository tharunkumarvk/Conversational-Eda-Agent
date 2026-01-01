"""
Supabase Storage Helper Module
Handles file uploads and downloads to/from Supabase cloud storage
"""

import os
import io
import tempfile
from typing import Optional, BinaryIO
from supabase import create_client, Client

try:
    from .config import settings
except ImportError:
    from config import settings

# Initialize Supabase client
supabase: Optional[Client] = None

def init_storage():
    """Initialize Supabase storage client"""
    global supabase
    try:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            print("⚠️ Supabase credentials not configured. Using local storage.")
            return False
        
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        print(f"✅ Supabase Storage initialized: {settings.SUPABASE_BUCKET}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize Supabase Storage: {e}")
        return False

def upload_file_to_storage(file_content: bytes, filename: str, content_type: str = "text/csv") -> tuple[bool, str]:
    """
    Upload file to Supabase Storage
    
    Args:
        file_content: File content as bytes
        filename: Name/path for the file in storage (e.g., "uuid_filename.csv")
        content_type: MIME type of the file
    
    Returns:
        (success: bool, public_url or error_message: str)
    """
    try:
        if not supabase:
            return False, "Supabase not initialized"
        
        # Upload to Supabase Storage
        response = supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
            path=filename,
            file=file_content,
            file_options={"content-type": content_type}
        )
        
        # Get public URL
        public_url = supabase.storage.from_(settings.SUPABASE_BUCKET).get_public_url(filename)
        
        print(f"✅ Uploaded to Supabase Storage: {filename}")
        return True, public_url
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Supabase upload error: {error_msg}")
        return False, error_msg

def download_file_from_storage(filename: str) -> tuple[bool, Optional[bytes], str]:
    """
    Download file from Supabase Storage
    
    Args:
        filename: Name/path of the file in storage
    
    Returns:
        (success: bool, file_content: bytes or None, error_message: str)
    """
    try:
        if not supabase:
            return False, None, "Supabase not initialized"
        
        # Download from Supabase Storage
        response = supabase.storage.from_(settings.SUPABASE_BUCKET).download(filename)
        
        if response:
            print(f"✅ Downloaded from Supabase Storage: {filename}")
            return True, response, ""
        else:
            return False, None, "File not found"
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Supabase download error: {error_msg}")
        return False, None, error_msg

def download_to_temp_file(filename: str) -> tuple[bool, Optional[str], str]:
    """
    Download file from Supabase Storage to a temporary local file
    Returns path to temp file that can be used with pandas.read_csv()
    
    Args:
        filename: Name/path of the file in storage
    
    Returns:
        (success: bool, temp_file_path: str or None, error_message: str)
    """
    try:
        success, content, error = download_file_from_storage(filename)
        if not success:
            return False, None, error
        
        # Create temp file
        temp_fd, temp_path = tempfile.mkstemp(suffix=os.path.splitext(filename)[1])
        with os.fdopen(temp_fd, 'wb') as temp_file:
            temp_file.write(content)
        
        print(f"✅ Saved to temp file: {temp_path}")
        return True, temp_path, ""
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Temp file error: {error_msg}")
        return False, None, error_msg

def delete_file_from_storage(filename: str) -> tuple[bool, str]:
    """
    Delete file from Supabase Storage
    
    Args:
        filename: Name/path of the file in storage
    
    Returns:
        (success: bool, error_message: str)
    """
    try:
        if not supabase:
            return False, "Supabase not initialized"
        
        response = supabase.storage.from_(settings.SUPABASE_BUCKET).remove([filename])
        
        print(f"✅ Deleted from Supabase Storage: {filename}")
        return True, ""
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Supabase delete error: {error_msg}")
        return False, error_msg

def list_files_in_storage(path: str = "") -> tuple[bool, list, str]:
    """
    List files in Supabase Storage bucket
    
    Args:
        path: Optional folder path to list files from
    
    Returns:
        (success: bool, file_list: list, error_message: str)
    """
    try:
        if not supabase:
            return False, [], "Supabase not initialized"
        
        response = supabase.storage.from_(settings.SUPABASE_BUCKET).list(path)
        
        return True, response, ""
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Supabase list error: {error_msg}")
        return False, [], error_msg

def cleanup_temp_file(temp_path: str):
    """Delete temporary file after use"""
    try:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            print(f"🗑️ Cleaned up temp file: {temp_path}")
    except Exception as e:
        print(f"⚠️ Could not cleanup temp file {temp_path}: {e}")
