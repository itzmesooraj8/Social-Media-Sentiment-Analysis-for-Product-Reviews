"""
Database Initialization / Migration Script.
Checks if tables exist, and creates them if not using the schema_dump.sql or 01_init_core.sql.
Intended for 'Senior Developer' handover automation.
"""
import os
import sys
import psycopg2
from urllib.parse import urlparse

# Add parent directory to path to allow imports if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_connection():
    # Attempt to find DATABASE_URL in env
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        # Fallback: Construct it from Supabase params if possible (unreliable without password)
        # But usually in deployment, DATABASE_URL is standard.
        # Let's check if SUPABASE_DB_URL is set (custom name)
        db_url = os.environ.get("SUPABASE_DB_URL")
    
    if not db_url:
        print("❌ Error: DATABASE_URL not found in environment variables.")
        print("   Please add DATABASE_URL=postgres://user:pass@host:port/postgres to your .env file.")
        print("   You can find this in Supabase Dashboard -> Settings -> Database -> Connection String.")
        return None

    try:
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def run_migrations():
    print("🚀 Starting Database Initialization...")
    
    conn = get_connection()
    if not conn:
        return

    # Path to SQL file
    sql_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sql", "01_init_core.sql")
    if not os.path.exists(sql_path):
        print(f"❌ Error: SQL file not found at {sql_path}")
        return
        
    try:
        with open(sql_path, "r", encoding="utf-8") as f:
            sql_content = f.read()
            
        with conn.cursor() as cur:
            # We assume the SQL file is safe and contains proper transaction logic or we control it.
            # 01_init_core.sql uses CREATE IF NOT EXISTS, so currently safe to rerun.
            cur.execute(sql_content)
        
        conn.commit()
        print("✅ Database schema initialized successfully.")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Load dotenv if running locally
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        load_dotenv(env_path)
    except ImportError:
        pass
        
    run_migrations()
