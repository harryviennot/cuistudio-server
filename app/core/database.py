"""
Supabase database client
"""
from functools import lru_cache
from supabase import Client, create_client
from app.core.config import get_settings
from fastapi import Request


@lru_cache()
def get_supabase_client() -> Client:
    """Get Supabase client instance (cached) - for admin operations"""
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLISHABLE_KEY)


def get_supabase_user_client(request: Request) -> Client:
    """
    Get Supabase client with user's JWT token for RLS-aware operations.
    This ensures auth.uid() is set correctly for RLS policies.
    """
    settings = get_settings()
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLISHABLE_KEY)

    # Extract JWT token from Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        # Set the JWT token for this client instance
        client.auth.set_session(token, token)  # Set both access and refresh to the same token

    return client


@lru_cache()
def get_supabase_admin_client() -> Client:
    """Get Supabase admin client with secret key (cached) - bypasses RLS"""
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SECRET_KEY)
