from supabase import create_client, Client
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Supabase Client Configuration
_supabase_client: Client | None = None

def get_supabase_client() -> Client:
    """
    Get or initialize the Supabase client.
    
    Returns:
        Client: Supabase client instance
        
    Raises:
        ValueError: If SUPABASE_URL or SUPABASE_KEY are not configured
    """
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise ValueError(
            "Supabase is not configured. Please set SUPABASE_URL and SUPABASE_KEY environment variables."
        )
    
    _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _supabase_client

def check_database_connection() -> bool:
    """
    Check if the database connection is alive.
    
    Uses Supabase Auth's get_session() as a lightweight health check
    that doesn't require any specific tables to exist.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        client = get_supabase_client()
        client.auth.get_session()
        logger.info("Database connection verified successfully")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False
