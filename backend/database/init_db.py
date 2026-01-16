"""
Initialize Supabase Database
Run this script to set up the database schema
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Supabase connection
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Service role key for admin operations

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def init_database():
    """Initialize database schema"""
    # Read SQL schema file
    with open("database/schema.sql", "r") as f:
        schema_sql = f.read()
    
    # Note: Supabase doesn't support direct SQL execution via Python client
    # You need to run the SQL in Supabase Dashboard > SQL Editor
    print("=" * 60)
    print("Database Schema Setup Instructions:")
    print("=" * 60)
    print("\n1. Go to your Supabase Dashboard")
    print("2. Navigate to SQL Editor")
    print("3. Copy and paste the contents of database/schema.sql")
    print("4. Run the SQL script")
    print("\n" + "=" * 60)
    print("\nSchema SQL:")
    print("=" * 60)
    print(schema_sql)
    print("=" * 60)

if __name__ == "__main__":
    init_database()







