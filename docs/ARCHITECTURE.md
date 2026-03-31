# Backend Architecture

## Overview

The CrackDSA backend is built with **FastAPI** and **Supabase**, using a clean, refactored architecture that eliminates code duplication and follows Django-inspired MVC patterns.

---

## Directory Structure

```
app/
├── main.py                        # FastAPI app initialization, CORS, route registration
├── config.py                      # Pydantic Settings (14 lines)
├── database.py                    # Supabase client management (24 lines)
├── dependencies.py                # Auth dependencies with DRY helpers (104 lines)
│
├── controllers/
│   └── roadmap_controller.py      # Roadmap generation orchestration
│
├── models/
│   ├── roadmap.py                 # Response schemas (Pydantic)
│   └── user_preferences.py        # Request schemas (Pydantic)
│
├── routes/
│   ├── auth_routes.py             # GET /me, POST /logout, GET /token-status (50 lines)
│   ├── test_routes.py             # Public, authenticated, optional-auth test endpoints
│   └── roadmap_routes.py          # POST /generate roadmap endpoint
│
├── services/
│   ├── ai_service.py              # Gemini LLM integration
│   └── roadmap_service.py         # Roadmap generation business logic
│
└── utils/
    ├── problem_loader.py          # Load problems.json with error handling
    └── validators.py              # Input validation
```

---

## Authentication Architecture (Refactored)

### Before Refactoring
- **Duplicate code**: Token extraction logic repeated in multiple functions
- **Duplicate code**: User data building logic repeated 2+ times
- **Unused files**: `auth_service.py`, `oauth_service.py`
- **Large functions**: `get_current_user()` was 80+ lines with all logic inline

### After Refactoring
- **DRY principle**: Helper functions `_extract_token_from_header()` and `_build_user_response()`
- **Cleaner code**: Dependencies reduced from ~195 lines to ~105 lines
- **Simplified routes**: `auth_routes.py` reduced from ~180 lines to ~50 lines
- **Centralized auth**: All auth logic in `app/dependencies.py`

### Key Files

#### `app/dependencies.py` (104 lines - was 195)
```python
# Helper functions (DRY principle)
def _extract_token_from_header(supabase_token, authorization):
    """Extract token from cookie or header - used by both get_current_user functions."""

def _build_user_response(user):
    """Build clean user data dict - used by both get_current_user functions."""

# Dependency functions
async def get_current_user(...):  # Protected route authentication
async def get_current_user_optional(...):  # Optional authentication
```

#### `app/routes/auth_routes.py` (50 lines - was 180)
```python
@router.get("/me")
async def me(user = Depends(get_current_user)):
    """Simple one-liner - all logic moved to dependencies.py"""
    return user

@router.post("/logout")
async def logout(response: Response):
    """Clear cookies."""

@router.get("/token-status")
async def token_status(user = Depends(get_current_user_optional)):
    """Check auth status using optional dependency."""
```

---

## Configuration Management (Cleaned)

### `app/config.py` (Before)
```python
DATABASE_URL: str = ""              # UNUSED - using Supabase only
OPENAI_API_KEY: str = ""            # UNUSED - using Gemini only
GEMINI_API_KEY: str = ""
SUPABASE_URL: str = ""
SUPABASE_KEY: str = ""
SUPABASE_SERVICE_ROLE_KEY: str = ""
```

### `app/config.py` (After - Cleaned)
```python
"""Application configuration from environment variables."""

class Settings(BaseSettings):
    """Application settings."""
    
    # Supabase Configuration
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    
    # AI Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"  # NEW: Configurable model
```

**Benefits**:
- Removed dead code (DATABASE_URL, OPENAI_API_KEY)
- Added configurable GEMINI_MODEL
- Used in `app/services/ai_service.py`

---

## Request Flow Examples

### Protected Route Request

```
Client (Frontend)
    ↓
1. Browser sends cookie or Authorization header with token
    ↓
FastAPI Route (e.g., POST /api/v1/roadmap/generate)
    ↓
2. Depends(get_current_user) triggered automatically
    ↓
get_current_user() in app/dependencies.py
    ↓
3. Calls _extract_token_from_header() → Get token
    ↓
4. Calls client.auth.get_user(token) → Verify with Supabase
    ↓
5. Calls _build_user_response(user) → Clean data dict
    ↓
6. Returns user dict to route handler
    ↓
Route handler receives user data in parameter
    ↓
Response sent back to client
```

### Optional Auth Request

```
Client (Optional Token)
    ↓
1. Depends(get_current_user_optional)
    ↓
get_current_user_optional() in app/dependencies.py
    ↓
2. Calls _extract_token_from_header() → Get token or None
    ↓
3. If no token, returns None immediately
    ↓
4. If token exists, calls client.auth.get_user(token) → Verify
    ↓
5. Returns user dict or None to route handler
    ↓
Route handler receives user dict or None
    ↓
Adapt response based on user presence
```

---

## Error Handling Improvements

### Before
- `problem_loader.py` would crash silently on JSON errors
- No logging for failures
- Generic exception handling

### After
- Specific error handling in `problem_loader.py`:
  ```python
  except FileNotFoundError:
      logger.error(f"Problems file not found: {PROBLEMS_FILE}")
      return []
  except json.JSONDecodeError as e:
      logger.error(f"Failed to parse problems JSON: {e}")
      return []
  ```
- Graceful degradation
- Clear error messages in logs

---

## Authentication Dependencies (How They Work)

### Using in Routes

```python
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user, get_current_user_optional
from typing import Dict, Any

router = APIRouter()

# Protected - user data injected automatically
@router.get("/protected")
async def protected(user: Dict[str, Any] = Depends(get_current_user)):
    return {"user_id": user['id'], "email": user['email']}

# Optional - user data injected, can be None
@router.get("/optional")
async def optional(user: Dict[str, Any] = Depends(get_current_user_optional)):
    if user:
        return {"message": f"Hello {user['full_name']}"}
    else:
        return {"message": "Hello guest"}

# Public - no dependencies
@router.get("/public")
async def public():
    return {"message": "Public endpoint"}
```

### Data Flow

1. **Token Extraction**:
   - Checks cookie first (`supabase_token`)
   - Falls back to Authorization header (`Bearer <token>`)
   - Returns None if neither found

2. **Token Verification**:
   - Calls `client.auth.get_user(token)`
   - Returns Supabase User object
   - Raises 401 if invalid

3. **User Data Building**:
   - Extracts metadata from User object
   - Converts datetimes to ISO strings
   - Returns clean dict with all fields

---

## Code Quality Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Dependencies.py | ~195 lines | ~105 lines | -46% |
| Auth routes | ~180 lines | ~50 lines | -72% |
| Config fields | 6 (2 unused) | 5 (all used) | -1 unused |
| Code duplication | 80+ lines | 0 lines | Eliminated |
| Error handling | Basic | Enhanced | Better logging |
| Configurable model | Hardcoded | settings.GEMINI_MODEL | Flexible |

---

## Dependencies

### Core
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **Pydantic Settings** - Config management

### Database & Auth
- **Supabase** - Database + authentication
- **Httpx** - Async HTTP client

### AI
- **Google Generative AI** - Gemini LLM

---

## Environment Variables Required

```env
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# AI
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.5-flash  # Optional

# Frontend (Optional)
FRONTEND_URL=https://your-frontend.com
```

---

## Testing

### Test Routes
- `GET /api/v1/test/public` - Public endpoint
- `GET /api/v1/test/authenticated` - Protected endpoint (requires token)
- `GET /api/v1/test/optional-auth` - Optional auth endpoint

### Testing Protected Route
```bash
# Get token from Supabase first
TOKEN="your_supabase_token"

# Test protected endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/test/authenticated
```

---

## Deployment Considerations

1. **CORS**: Update `FRONTEND_URL` environment variable
2. **Database**: Supabase handles automatically
3. **Authentication**: Supabase OAuth configured in dashboard
4. **Health Checks**: Use `GET /health` for monitoring
5. **Logging**: Review logs for errors and warnings

---

## Future Improvements

- [ ] Add request rate limiting
- [ ] Implement role-based access control (RBAC)
- [ ] Add API key authentication option
- [ ] Implement request/response logging middleware
- [ ] Add performance metrics collection
- [ ] Cache Supabase session tokens
- [ ] Implement request timeout handling
