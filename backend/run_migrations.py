
import os
import psycopg2
from psycopg2 import errors
from dotenv import load_dotenv
import re

def run_migrations():
    """Connects to the Supabase database and runs SQL migration scripts."""

    try:
        # Load environment variables from .env file in the root directory
        from pathlib import Path
        env_path = Path(__file__).parent.parent / ".env"
        load_dotenv(dotenv_path=env_path)

        supabase_url = os.getenv("SUPABASE_URL")
        db_password = os.getenv("SUPABASE_DB_PASSWORD") # User needs to add this to .env

        if not supabase_url or not db_password:
            print("ERROR: SUPABASE_URL and SUPABASE_DB_PASSWORD must be set in your .env file.")
            print("You can find your database password in your Supabase project settings under Database.")
            return

        # Extract the project reference from the URL
        project_ref_match = re.search(r"https://(.+?)\.supabase\.co", supabase_url)
        if not project_ref_match:
            print(f"ERROR: Could not parse project reference from SUPABASE_URL: {supabase_url}")
            return

        project_ref = project_ref_match.group(1)

        # Database connection details
        db_host = f"db.{project_ref}.supabase.co"
        db_name = "postgres"
        db_user = "postgres"

        print(f"Connecting to database host: {db_host}...")

        # Connect to the database
        conn = psycopg2.connect(
            host=db_host,
            dbname=db_name,
            user=db_user,
            password=db_password,
            port=5432
        )
        print("Database connection successful.")

        cursor = conn.cursor()

        # Get the list of SQL files to execute
        sql_dir = os.path.join(os.path.dirname(__file__), 'sql')
        sql_files = [
            '01_init_core.sql',
            '01_add_features.sql',
            '01_add_hash.sql',
            '02_security_hardening.sql',
            '03_production_upgrade.sql',
            '04_finalize_production.sql',
            '05_add_youtube_comments.sql',
            '06_add_roles.sql',
            '07_add_engagement_metrics.sql',
            'security.sql'
        ]

        success = True
        for sql_file in sql_files:
            file_path = os.path.join(sql_dir, sql_file)
            if os.path.exists(file_path):
                print(f"Running migration: {sql_file}...")
                with open(file_path, 'r') as f:
                    sql_query = f.read()
                    # Remove comments from the SQL query
                    sql_query = re.sub(r'--.*$', '', sql_query, flags=re.MULTILINE)
                    if sql_query.strip():
                        try:
                            cursor.execute(sql_query)
                            print(f"Successfully executed {sql_file}.")
                        except psycopg2.errors.DuplicateObject:
                            print(f"Object in {sql_file} already exists, skipping.")
                            conn.rollback()
                        except psycopg2.Error as e:
                            print(f"Error executing {sql_file}: {e}")
                            conn.rollback()
                            success = False
                    else:
                        print(f"Skipping empty or comment-only file: {sql_file}.")
            else:
                print(f"WARNING: Migration file not found: {sql_file}")

        # Commit the changes and close the connection
        conn.commit()
        cursor.close()
        conn.close()
        if success:
            print("All migrations completed successfully!")
        else:
            print("Some migrations failed. Please check the logs.")

    except psycopg2.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    run_migrations()
