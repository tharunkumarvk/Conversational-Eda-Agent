"""
Database Migration Script - SQLite to PostgreSQL
Migrates your local SQLite data to cloud PostgreSQL database
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def migrate_database():
    """
    Migrate data from SQLite to Supabase PostgreSQL
    """
    print("🔄 Starting database migration from SQLite to Supabase...\n")
    
    # Import models
    try:
        from db import Base, Dataset, ChatHistory, PlotHistory
    except ImportError:
        from backend.db import Base, Dataset, ChatHistory, PlotHistory
    
    # Source: SQLite
    source_db = "sqlite:///./backend/eda_agent.db"
    
    # Target: Supabase (from .env)
    from dotenv import load_dotenv
    load_dotenv()
    target_db = os.getenv("DATABASE_URL")
    
    if not target_db or "sqlite" in target_db.lower():
        print("❌ Error: DATABASE_URL in .env is not set to Supabase!")
        print("Current:", target_db)
        sys.exit(1)
    
    print(f"📍 Source: SQLite (./backend/eda_agent.db)")
    print(f"🌐 Target: Supabase PostgreSQL")
    print(f"   {target_db[:60]}...\n")
    
    # Create engines
    source_engine = create_engine(source_db)
    target_engine = create_engine(target_db)
    
    # Create sessions
    SourceSession = sessionmaker(bind=source_engine)
    TargetSession = sessionmaker(bind=target_engine)
    
    source_session = SourceSession()
    target_session = TargetSession()
    
    try:
        # Migrate Dataset table
        print("📦 Migrating datasets...")
        datasets = source_session.query(Dataset).all()
        for ds in datasets:
            # Check if already exists
            existing = target_session.query(Dataset).filter(Dataset.file_id == ds.file_id).first()
            if not existing:
                new_ds = Dataset(
                    file_id=ds.file_id,
                    filename=ds.filename,
                    file_path=ds.file_path,
                    upload_time=ds.upload_time,
                    rows=ds.rows,
                    columns=ds.columns,
                    size_bytes=ds.size_bytes
                )
                target_session.add(new_ds)
        target_session.commit()
        print(f"   ✅ Migrated {len(datasets)} datasets")
        
        # Migrate ChatHistory table
        print("💬 Migrating chat history...")
        chats = source_session.query(ChatHistory).all()
        migrated_chats = 0
        for chat in chats:
            # Check if already exists
            existing = target_session.query(ChatHistory).filter(ChatHistory.id == chat.id).first()
            if not existing:
                new_chat = ChatHistory(
                    user_query=chat.user_query,
                    ai_response=chat.ai_response,
                    file_id=chat.file_id,
                    ts=chat.ts
                )
                target_session.add(new_chat)
                migrated_chats += 1
        target_session.commit()
        print(f"   ✅ Migrated {migrated_chats} chat messages")
        
        # Migrate PlotHistory table
        print("📊 Migrating plot history...")
        plots = source_session.query(PlotHistory).all()
        migrated_plots = 0
        for plot in plots:
            # Check if already exists
            existing = target_session.query(PlotHistory).filter(PlotHistory.id == plot.id).first()
            if not existing:
                new_plot = PlotHistory(
                    file_id=plot.file_id,
                    plot_name=plot.plot_name,
                    plot_type=getattr(plot, 'plot_type', None),
                    plot_base64=getattr(plot, 'plot_base64', None),
                    ts=plot.ts
                )
                target_session.add(new_plot)
                migrated_plots += 1
        target_session.commit()
        print(f"   ✅ Migrated {migrated_plots} plot records")
        
        print("\n🎉 Migration completed successfully!")
        print(f"   📊 Total: {len(datasets)} datasets, {migrated_chats} chats, {migrated_plots} plots")
        print("\n✅ Your data is now in Supabase cloud database!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        target_session.rollback()
        sys.exit(1)
    finally:
        source_session.close()
        target_session.close()

if __name__ == "__main__":
    migrate_database()
