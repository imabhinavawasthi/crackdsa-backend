from supabase import create_client, Client
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Supabase Client Configuration
_supabase_client: Client | None = None

def get_supabase_client(jwt_token: str = None) -> Client:
    """
    Get or initialize a Supabase client.
    
    If jwt_token is provided, returns a NEW client instance scoped to that user.
    This ensures that Supabase Row-Level Security (RLS) is correctly enforced
    for the specific authenticated user.
    
    Returns:
        Client: Supabase client instance
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise ValueError(
            "Supabase is not configured. Please set SUPABASE_URL and SUPABASE_KEY environment variables."
        )

    # 1. Scoped User Client (RLS-enabled)
    # Uses the Anon Key + User JWT
    if jwt_token:
        # Create a new client instance for the specific request context
        # We use the ANON_KEY (settings.SUPABASE_KEY) for RLS
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        client.postgrest.auth(jwt_token)
        return client

    # 2. Administrative/Global Client (RLS-bypass)
    # Uses the Service Role Key for background/admin tasks
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    
    # Preferred: Use Service Role Key for admin operations if available
    admin_key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY
    _supabase_client = create_client(settings.SUPABASE_URL, admin_key)
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
