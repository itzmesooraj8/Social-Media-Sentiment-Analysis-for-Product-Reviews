import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

def setup_reports():
    print("🚀 Setting up Persistant Reports...")
    
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ Error: DATABASE_URL not found in environment variables.")
        return

    sql_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sql", "08_add_reports.sql")
    
    try:
        conn = psycopg2.connect(db_url)
        with open(sql_path, "r", encoding="utf-8") as f:
            sql_content = f.read()
            
        with conn.cursor() as cur:
            cur.execute(sql_content)
        
        conn.commit()
        print("✅ Reports table and policies created successfully.")
        conn.close()
    except Exception as e:
        print(f"❌ Setup failed: {e}")

if __name__ == "__main__":
    setup_reports()
