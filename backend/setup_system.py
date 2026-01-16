import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def install_spacy_model():
    print("⬇️  Checking/Installing Spacy 'en_core_web_sm' model...")
    try:
        import spacy
        if not spacy.util.is_package("en_core_web_sm"):
            subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
            print("✅ Spacy model installed.")
        else:
            print("✅ Spacy model already present.")
    except Exception as e:
        print(f"❌ Failed to check/install Spacy model: {e}")

def run_sql_file(supabase: Client, file_path: Path):
    print(f"📄 Applying SQL: {file_path.name}...")
    try:
        if not file_path.exists():
            print(f"⚠️  File not found: {file_path}")
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
            
        # Supabase-py doesn't support raw SQL execution directly via client easily without RLS bypass
        # But we can use the REST API via the client postgrest features if setup, 
        # or more reliably, we rely on the user running this in SQL Editor if this fails.
        # However, for a python script, we can try to use a direct connection if we had psycopg2.
        # Given the constraints, we will assume the user has set up the DB or we print instructions.
        
        # ACTUALLY: The best way for the client is to use the dashboard, OR use a postgres connection string.
        # Since we only have HTTP client, we will print the content for them to run IF we can't execute.
        # BUT, let's try to see if we can use a "rpc" call if one exists to exec sql? No.
        
        print(f"   ℹ️  Please copy content of {file_path.name} to Supabase SQL Editor if tables don't exist.")
    except Exception as e:
        print(f"❌ Error reading SQL file: {e}")

def main():
    print("🚀 Starting System Setup...")
    
    # 1. Install AI Model
    install_spacy_model()

    # 2. Check Database Connection
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") # Must use Service Role to modify DB structure
    
    if not url or not key:
        print("❌ Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing in .env")
        return

    try:
        supabase: Client = create_client(url, key)
        # Simple health check
        supabase.table("products").select("count", count="exact").execute()
        print("✅ Supabase connection successful.")
    except Exception as e:
        print("⚠️  Database Warning: Could not connect to 'products' table. It might not exist yet.")
        print(f"   Connection details: URL={url}")

    # 3. Reminder for SQL
    print("\n" + "="*50)
    print("📝 DATABASE SETUP REQUIRED")
    print("="*50)
    print("To finish the setup, please go to your Supabase Dashboard -> SQL Editor")
    print("and run the contents of these files in this order:")
    print("1. backend/sql/01_init_core.sql")
    print("2. backend/schema.sql")
    print("3. backend/sql/05_add_alerts_settings_topics.sql (if exists)")
    print("="*50)

if __name__ == "__main__":
    main()
