"""
Supabase database client
"""
from functools import lru_cache
from supabase import Client, create_client
from app.core.config import get_settings


@lru_cache()
def get_supabase_client() -> Client:
    """Get Supabase client instance (cached)"""
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLISHABLE_KEY)


@lru_cache()
def get_supabase_admin_client() -> Client:
    """Get Supabase admin client with secret key (cached)"""
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SECRET_KEY)
