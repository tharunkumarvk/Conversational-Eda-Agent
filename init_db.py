"""Initialize Database - Create all tables in PostgreSQL/Supabase"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from db import Base, engine

def init_database():
    """Create all database tables"""
    print("🔄 Creating database tables...")
    try:
        Base.metadata.create_all(engine)
        print("✅ Tables created successfully!")
        print("\nTables created:")
        print("  📊 dataset - Stores uploaded file metadata")
        print("  💬 chathistory - Stores AI chat conversations")
        print("  📈 plothistory - Stores generated plot metadata")
        print("\n🎉 Database initialized! You can now:")
        print("  1. Upload files through the frontend")
        print("  2. View tables in Supabase dashboard → Table Editor")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    init_database()
