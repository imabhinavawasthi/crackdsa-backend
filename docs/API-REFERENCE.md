# CrackDSA Backend API Reference

## Overview

Complete API endpoint reference for the CrackDSA backend. All endpoints are live at `http://localhost:8000` (development) or your deployed URL.

**API Version**: 0.1.0  
**Base URL**: `/api/v1` for most endpoints  
**Documentation URL**: `http://localhost:8000/docs` (Swagger UI)  

---

## Authentication

### Token Sources
Endpoints requiring authentication accept tokens from two sources:

1. **HTTP-only Cookie** (set by frontend after OAuth)
   ```
   Cookie: supabase_token=eyJ0eXAi...
   ```

2. **Authorization Header** (for API clients)
   ```
   Authorization: Bearer eyJ0eXAi...
   ```

### Authentication Dependencies
- `Depends(get_current_user)` - Required authentication (returns 401 if missing)
- `Depends(get_current_user_optional)` - Optional authentication (returns user or None)

See `app/dependencies.py` for implementation.

---

## Endpoints

### Health Check
**Public - No Authentication Required**

#### GET /health

Real-time status of API and database connectivity.

**Response (HTTP 200)**:
```json
{
  "status": "ok",
  "database": "connected",
  "timestamp": "2026-03-30T10:15:30Z"
}
```

**Response (HTTP 503 - Degraded)**:
```json
{
  "status": "degraded",
  "database": "disconnected",
  "timestamp": "2026-03-30T10:15:32Z"
}
```

**Use Cases**: Monitoring, load balancer health checks, Kubernetes probes

---

### Authentication Endpoints
**Base Path**: `/api/v1/auth`

#### GET /api/v1/auth/me
Get current authenticated user data.

**Authentication**: Required ✅  
**Parameters**: None (token from cookie or header)

**Response (HTTP 200)**:
```json
{
  "id": "96718f5f-3083-467f-8e45-980b5a6db8d1",
  "email": "user@example.com",
  "full_name": "John Doe",
  "avatar_url": "https://lh3.googleusercontent.com/...",
  "email_verified": true,
  "phone": "+1234567890",
  "provider": "google",
  "created_at": "2024-03-24T08:28:53.784675",
  "last_sign_in_at": "2026-03-29T19:56:18.135833",
  "updated_at": "2026-03-29T19:56:18.155501"
}
```

**Error (HTTP 401 - No Token)**:
```json
{
  "detail": "No authentication token provided"
}
```

**Error (HTTP 401 - Invalid Token)**:
```json
{
  "detail": "Invalid or expired token"
}
```

**Examples**:
```bash
# Using Authorization header
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/auth/me

# Using cookie (browser will send automatically)
curl -H "Cookie: supabase_token=YOUR_TOKEN" http://localhost:8000/api/v1/auth/me
```

---

#### POST /api/v1/auth/logout
Clear authentication tokens and logout user.

**Authentication**: Optional  
**Parameters**: None

**Response (HTTP 200)**:
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

**Frontend Flow**:
```javascript
// 1. Logout from Supabase
await supabase.auth.signOut();

// 2. Clear backend cookies
await fetch('/api/v1/auth/logout', { method: 'POST' });
```

---

#### GET /api/v1/auth/token-status
Check if user has a valid authentication token.

**Authentication**: Optional  
**Parameters**: None

**Response (HTTP 200 - Authenticated)**:
```json
{
  "authenticated": true
}
```

**Response (HTTP 200 - Not Authenticated)**:
```json
{
  "authenticated": false
}
```

---

### Test Endpoints
**Base Path**: `/api/v1/test`

#### GET /api/v1/test/public
Public test endpoint - no authentication required.

**Authentication**: No  
**Response (HTTP 200)**:
```json
{
  "message": "This is a public endpoint",
  "requires_auth": false,
  "status": "success"
}
```

**Example**:
```bash
curl http://localhost:8000/api/v1/test/public
```

---

#### GET /api/v1/test/authenticated
Protected test endpoint - returns user data.

**Authentication**: Required ✅  
**Response (HTTP 200)**:
```json
{
  "message": "Hello John Doe! You are authenticated",
  "requires_auth": true,
  "user": {
    "id": "96718f5f-3083-467f-8e45-980b5a6db8d1",
    "email": "user@example.com",
    "full_name": "John Doe",
    "avatar_url": "https://...",
    "email_verified": true,
    "phone": "+1234567890",
    "provider": "google",
    "created_at": "2024-03-24T08:28:53.784675",
    "last_sign_in_at": "2026-03-29T19:56:18.135833",
    "updated_at": "2026-03-29T19:56:18.155501"
  }
}
```

**Error (HTTP 401)**:
```json
{
  "detail": "No authentication token provided"
}
```

**Example**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/test/authenticated
```

---

#### GET /api/v1/test/optional-auth
Endpoint with optional authentication - works both authenticated and unauthenticated.

**Authentication**: Optional  
**Response (HTTP 200 - Authenticated)**:
```json
{
  "message": "Welcome back, John Doe!",
  "is_authenticated": true,
  "user": { ... user data ... }
}
```

**Response (HTTP 200 - Unauthenticated)**:
```json
{
  "message": "Welcome guest! Sign in to see personalized content",
  "is_authenticated": false,
  "user": null
}
```

**Examples**:
```bash
# Without token (guest)
curl http://localhost:8000/api/v1/test/optional-auth

# With token (authenticated)
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/test/optional-auth
```

---

### Roadmap Generation Endpoints
**Base Path**: `/api/v1/roadmap`

#### POST /api/v1/roadmap/generate
Generate a personalized DSA learning roadmap.

**Authentication**: Optional  
**Request Body**:
```json
{
  "preparation_goal": "placements",
  "target_companies": ["google", "amazon"],
  "current_dsa_level": "intermediate",
  "timeline_days": 90,
  "hours_per_day": 4,
  "preferred_language": "python",
  "strong_topics": ["arrays", "hashing"],
  "weak_topics": ["dynamic_programming", "graphs"]
}
```

**Response (HTTP 200)**:
```json
{
  "total_days": 90,
  "days": [
    {
      "day": 1,
      "topic": "arrays",
      "tasks": [
        {
          "problem_id": "two_sum",
          "title": "Two Sum",
          "difficulty": "easy"
        }
      ],
      "revision": []
    }
  ]
}
```

**Note**: For authenticated requests, user data can be injected into the roadmap generation logic.

---

## Common Implementation Patterns

### Protecting Routes

In your route file (`app/routes/your_routes.py`):

```python
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from typing import Dict, Any

router = APIRouter()

@router.get("/protected")
async def protected_endpoint(user: Dict[str, Any] = Depends(get_current_user)):
    """This endpoint requires authentication."""
    return {
        "message": f"Hello {user['full_name']}",
        "user_id": user['id']
    }
```

### Optional Authentication

```python
from app.dependencies import get_current_user_optional
from typing import Optional

@router.get("/mixed")
async def mixed_endpoint(user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """This endpoint works with or without authentication."""
    if user:
        return {"content": "personalized", "user": user['email']}
    else:
        return {"content": "generic"}
```

### Accessing User in Request Body

```python
from pydantic import BaseModel

class MyRequest(BaseModel):
    title: str
    description: str

@router.post("/create")
async def create_item(
    item: MyRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """User data available alongside request body."""
    return {
        "item": item,
        "created_by": user['email'],
        "user_id": user['id']
    }
```

---

## Error Responses

### 400 - Bad Request
```json
{
  "detail": "Invalid request format"
}
```

### 401 - Unauthorized
```json
{
  "detail": "No authentication token provided"
}
```

### 403 - Forbidden
```json
{
  "detail": "Insufficient permissions"
}
```

### 404 - Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 - Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

Currently no rate limiting is implemented. For production, consider adding:
- API key-based rate limiting
- Per-user rate limits
- IP-based rate limiting

---

## CORS Configuration

CORS is enabled for local development URLs:
- `http://localhost:3000`
- `http://localhost:3001`
- `http://127.0.0.1:3000`

For production deployment, set `FRONTEND_URL` environment variable:
```env
FRONTEND_URL=https://your-frontend-domain.com
```

---

## Testing Endpoints with cURL

### Test Public Endpoint
```bash
curl http://localhost:8000/api/v1/test/public
```

### Test Health Check
```bash
curl http://localhost:8000/health
```

### Test Authenticated Endpoint (get token first)
```bash
# 1. Login via frontend to get token
# 2. Set YOUR_TOKEN to the access token

curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/test/authenticated
```

### Test Optional Auth
```bash
# Without token
curl http://localhost:8000/api/v1/test/optional-auth

# With token
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/test/optional-auth
```

---

## Interactive API Documentation

**Swagger UI**: http://localhost:8000/docs  
**ReDoc**: http://localhost:8000/redoc

Try out endpoints interactively in these UI tools!
