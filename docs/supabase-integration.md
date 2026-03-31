# Supabase Integration Guide

## Overview

This document describes the integration of **Supabase** as the primary database and authentication provider for the CrackDSA backend. Supabase replaces SQLAlchemy with SQLite/PostgreSQL and provides built-in authentication with Google OAuth support.

**Last Updated**: March 29, 2026

## Architecture

### Database Connection
- **Provider**: Supabase (PostgreSQL backend)
- **Python Client**: `supabase-py`
- **Configuration**: Environment variables (`SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_ROLE_KEY`)
- **Connection**: Lazy-initialized singleton via `get_supabase_client()`

### Authentication
- **Type**: JWT tokens issued by Supabase Auth
- **OAuth Providers**: Google Login (configured in Supabase console)
- **Middleware**: FastAPI dependencies for token verification
- **Protection**: Optional on routes via `Depends(get_current_user)`

## Setup Instructions

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up
2. Create a new project:
   - Choose region closest to your deployment
   - Set a strong database password
   - Wait for project initialization (~2 minutes)
3. Navigate to **Settings → API** to get credentials:
   - `Project URL` → Use as `SUPABASE_URL`
   - `Anon Public Key` → Use as `SUPABASE_KEY`
   - `Service Role Secret` → Use as `SUPABASE_SERVICE_ROLE_KEY` (admin operations only)

### 2. Configure Google OAuth (Optional)

1. In Supabase console, go to **Authentication → Providers**
2. Enable **Google**:
   - Create OAuth app in [Google Cloud Console](https://console.cloud.google.com)
   - Get Client ID and Client Secret
   - Paste into Supabase Google provider settings
   - Add authorized redirect URI: `https://your-project.supabase.co/auth/v1/callback`

### 3. Set Environment Variables

Create `.env` file in project root:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# API Keys
GEMINI_API_KEY=AIzaSy...
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

The `supabase` package is already listed in `requirements.txt`.

## Architecture Files

### [app/database.py](../app/database.py)
**Supabase Client Management**

Functions:
- `get_supabase_client()` → Returns singleton Supabase client instance
- `check_database_connection()` → Verifies database accessibility for health checks (uses auth endpoint for lightweight testing)

```python
from app.database import get_supabase_client, check_database_connection

# Initialize client
client = get_supabase_client()

# Check connection (uses Supabase Auth for lightweight verification)
is_connected = check_database_connection()
```

### [app/config.py](../app/config.py)
**Configuration Management**

Settings class with Pydantic v2:
```python
class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    GEMINI_API_KEY: str
    # ... other settings
```

Environment variables are automatically loaded from `.env` file.

### [app/dependencies.py](../app/dependencies.py)
**Centralized authentication dependencies**

Functions:
- `_extract_token_from_header()` → Helper to get token from cookie or header
- `_build_user_response()` → Helper to construct clean user data dict
- `get_current_user()` → FastAPI dependency for protected routes (returns 401 if no token)
- `get_current_user_optional()` → FastAPI dependency for optional auth (returns None if no token)

```python
from app.dependencies import get_current_user, get_current_user_optional

# Protected route
@router.get("/protected")
async def protected(user = Depends(get_current_user)):
    return {"user_id": user['id']}

# Optional auth
@router.get("/optional")
async def optional(user = Depends(get_current_user_optional)):
    if user:
        return {"message": f"Hello {user['full_name']}"}
    else:
        return {"message": "Hello guest"}
```

---

## API Endpoints

For complete API endpoint documentation, see **[API-REFERENCE.md](API-REFERENCE.md)**.

**Key endpoints**:
- `GET /health` - Health check (public)
- `GET /api/v1/auth/me` - Get current user (protected)
- `POST /api/v1/auth/logout` - Logout (optional auth)
- `GET /api/v1/auth/token-status` - Check auth status (optional auth)
- `POST /api/v1/roadmap/generate` - Generate roadmap (optional auth)

## Protecting Routes with Authentication

### Example 1: Fully Protected Endpoint

```python
from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_user

router = APIRouter()

@router.get("/user/profile")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Only authenticated users can access this endpoint.
    Requires: Authorization: Bearer <JWT_TOKEN>
    """
    return {
        "user_id": current_user.get("sub"),
        "email": current_user.get("email")
    }
```

Client usage:
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  http://localhost:8000/user/profile
```

### Example 2: Optional Authentication

```python
from typing import Optional
from app.middleware.auth import get_current_user_optional

@router.get("/public-data")
async def get_public_data(current_user: Optional[dict] = Depends(get_current_user_optional)):
    """
    Works with or without authentication.
    Returns personalized data if authenticated, generic data otherwise.
    """
    if current_user:
        return {
            "data": "personalized",
            "user_email": current_user.get("email"),
            "content": [...]  # User-specific recommendations
        }
    else:
        return {
            "data": "public",
            "user_email": None,
            "content": [...]  # Generic content
        }
```

## Database Operations

### Using Supabase Client Directly

**Read Data**:
```python
from app.database import get_supabase_client

client = get_supabase_client()

# Select all from table
response = client.table("users").select("*").execute()
users = response.data

# With filters
response = client.table("users").select("*").eq("status", "active").execute()
active_users = response.data
```

**Insert Data**:
```python
response = client.table("users").insert({
    "email": "user@example.com",
    "name": "John Doe",
    "preferences": {"theme": "dark"}
}).execute()

new_user = response.data[0]
```

**Update Data**:
```python
response = client.table("users").update({
    "name": "Jane Doe"
}).eq("id", user_id).execute()
```

**Delete Data**:
```python
response = client.table("users").delete().eq("id", user_id).execute()
```

### Async Operations

All Supabase operations are currently synchronous but can be wrapped in async context:

```python
import asyncio
from app.database import get_supabase_client

async def get_user_async(user_id: str):
    """Wrap synchronous operation in async function."""
    loop = asyncio.get_event_loop()
    client = get_supabase_client()
    
    response = await loop.run_in_executor(
        None,
        lambda: client.table("users").select("*").eq("id", user_id).execute()
    )
    return response.data[0] if response.data else None
```

## Startup Verification

When the app starts, it automatically:

1. **Initializes Supabase client** with credentials from environment
2. **Verifies database connection** with a test query
3. **Logs initialization status** to console
4. **Raises error if credentials missing** (app will not start without `SUPABASE_URL` and `SUPABASE_KEY`)

Startup logs:
```
INFO:     FastAPI service starting...
INFO:     Supabase client initialized successfully
INFO:     Database connection verified - service ready
```

If database is unreachable:
```
ERROR:    Database connection check failed: Connection timeout
WARNING: Database connection check failed - service may not be fully operational
```

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `ValueError: Supabase is not configured` | Missing `SUPABASE_URL` or `SUPABASE_KEY` | Set environment variables and restart |
| `Connection timeout` | Supabase project paused or network unreachable | Check Supabase dashboard, verify internet connection |
| `401 Unauthorized on protected route` | Missing or invalid JWT token | Include valid token in `Authorization: Bearer <token>` header |
| `HTTPException 503 from /health` | Database offline | Wait for Supabase recovery or check project status |

### Error Response Format

Authentication failures return:
```json
{
  "detail": "Invalid authentication credentials"
}
```

HTTP status: **401 Unauthorized**

## Monitoring & Logging

### Health Endpoint for Monitoring

Set up monitoring tool to periodically call `GET /health`:

```bash
# Every 30 seconds
watch -n 30 'curl -s http://localhost:8000/health | jq .'
```

### Application Logs

View Supabase-related logs:
```bash
# Start app with logging
PYTHONUNBUFFERED=1 uvicorn app.main:app --reload --log-level info
```

Key log patterns:
- `Supabase client initialized successfully` → Connection OK
- `Database connection verified` → Ready to serve
- `Database connection check failed` → Potential issues

## Performance Considerations

### Connection Pooling
Supabase client automatically manages connection pooling. No additional configuration needed.

### Response Caching
For read-heavy operations, consider implementing caching:

```python
from functools import lru_cache
import asyncio

# Simple in-memory cache (development only)
@lru_cache(maxsize=128)
def get_cached_problem(problem_id: str):
    client = get_supabase_client()
    response = client.table("problems").select("*").eq("id", problem_id).execute()
    return response.data[0] if response.data else None

# Clear cache after updates
def clear_problem_cache():
    get_cached_problem.cache_clear()
```

### Rate Limiting
Supabase has rate limits on free tier. Implement rate limiting middleware if needed:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

## Migration from SQLAlchemy

See [MIGRATION_GUIDE.md](../MIGRATION_GUIDE.md) for detailed steps on:
- Migrating existing database schema to Supabase
- Refactoring SQLAlchemy ORM code to Supabase client
- User data migration strategies

## Deployment Checklist

- [ ] Supabase project created and initialized
- [ ] Google OAuth configured (if using social login)
- [ ] Environment variables set in production:
  - `SUPABASE_URL`
  - `SUPABASE_KEY`
  - `SUPABASE_SERVICE_ROLE_KEY` (admin/automation only, not in client requests)
- [ ] Health endpoint accessible: `GET /health` returns 200
- [ ] Database connection verified on startup (check logs)
- [ ] Protected endpoints reject unauthenticated requests (401)
- [ ] Supabase project backups configured
- [ ] Monitoring alerts set up for health endpoint

## References

- [Supabase Python Client Docs](https://supabase.com/docs/reference/python)
- [Supabase Authentication](https://supabase.com/docs/guides/auth)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT (JSON Web Tokens)](https://jwt.io)
