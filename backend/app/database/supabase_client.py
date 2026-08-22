from functools import lru_cache
from typing import Optional
from supabase import Client, create_client
from app.config import get_settings
from app.utils.logger import logger


@lru_cache
def get_supabase_client() -> Optional[Client]:
    """
    Returns an initialized Supabase Client if credentials are configured.
    Returns None if credentials are placeholder / empty (allowing in-memory repo fallback).
    """
    settings = get_settings()
    url = settings.SUPABASE_URL.strip()
    key = settings.SUPABASE_KEY.strip()

    if not url or not key or "your-project" in url or "demo-civicai" in url:
        logger.info("Supabase client initialized in fallback/in-memory mode (credentials not configured for live cloud).")
        return None

    try:
        client = create_client(url, key)
        logger.info(f"Supabase client connected to {url}")
        return client
    except Exception as e:
        logger.warning(f"Failed to connect to Supabase: {e}. Falling back to local mode.")
        return None
