"""Test Supabase Database Connection"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

def test_connection():
    """Test database connection to Supabase"""
    print("🔄 Testing Supabase connection...\n")
    
    try:
        from config import settings
        from sqlalchemy import create_engine, text
        
        print(f"📍 Database URL: {settings.DATABASE_URL[:50]}...")
        
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected successfully!")
            print(f"📊 PostgreSQL Version: {version[:80]}...\n")
            
            # Check if tables exist
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print(f"✅ Found {len(tables)} tables:")
                for table in tables:
                    print(f"   📊 {table}")
            else:
                print("⚠️  No tables found. Run: python init_db.py")
                
        return True
        
    except Exception as e:
        print(f"❌ Connection failed!")
        print(f"Error: {e}\n")
        print("💡 Common fixes:")
        print("  1. Check password has no typos")
        print("  2. Special characters in password must be URL-encoded:")
        print("     @ → %40")
        print("     # → %23")
        print("     $ → %24")
        print("  3. Check Supabase project is active")
        print("  4. Verify connection string from Supabase dashboard")
        return False

if __name__ == "__main__":
    if test_connection():
        print("\n🎉 Database is ready to use!")
    else:
        print("\n❌ Please fix connection issues above")
        sys.exit(1)
