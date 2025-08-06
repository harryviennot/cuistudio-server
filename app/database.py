import os
from supabase import create_client, Client
from dotenv import load_dotenv
from app.config import Settings

load_dotenv()

# Supabase configuration
SUPABASE_URL = Settings.SUPABASE_URL
SUPABASE_PUBLISHABLE_KEY = Settings.SUPABASE_PUBLISHABLE_KEY

if not SUPABASE_URL or not SUPABASE_PUBLISHABLE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY must be set in environment variables")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY)

def get_supabase_client() -> Client:
    """Get the Supabase client instance"""
    return supabase 