# Role-Based Access Control (RBAC)

## Overview

The backend implements role-based access control to restrict API endpoints to users with specific roles. Roles are defined via environment variables and mapped to user emails.

---

## Configuration

### Adding Roles to `.env`

Roles are configured as comma-separated email lists in environment variables following the pattern `ROLE_<ROLENAME>`.

```env
# Admin role - comma-separated emails
ROLE_ADMIN=a@crackdsa.com,b@crackdsa.com

# Support team role
ROLE_SUPPORT_TEAM=support1@crackdsa.com,support2@crackdsa.com

# Moderator role
ROLE_MODERATOR=moderator1@crackdsa.com

# You can add any custom roles following the ROLE_ pattern
ROLE_CUSTOM_TEAM=user1@company.com,user2@company.com
```

### Dynamic Role Discovery

Roles are automatically parsed from the environment on startup:
- Any variable starting with `ROLE_` is treated as a role definition
- The role name is the part after `ROLE_` (lowercased)
- Example: `ROLE_ADMIN` → role name is `admin`

---

## Architecture

### Role Lookup Flow

```
User Authentication
    ↓
Token validated via Supabase
    ↓
User email extracted
    ↓
Email looked up in role mappings (config.role_mapping)
    ↓
User roles list returned
    ↓
Role dependency checks against required roles
    ↓
Access granted/denied (403 if insufficient permissions)
```

### Helper Functions

#### `_get_user_roles(email: str) -> List[str]`
- Internal function to get all roles for a user
- Checks user email against all role mappings
- Returns empty list if user has no roles

---

## Dependencies

### 1. `get_current_user_with_roles()`
Returns authenticated user data with their roles included.

```python
from app.dependencies import get_current_user_with_roles

@router.get("/my-roles")
async def get_my_roles(user = Depends(get_current_user_with_roles)):
    return {
        "email": user['email'],
        "roles": user['roles'],
        "has_admin": "admin" in user['roles'],
    }
```

**Returns:**
```json
{
  "id": "user-id",
  "email": "admin@crackdsa.com",
  "full_name": "Admin User",
  "roles": ["admin"],
  // ... other user fields
}
```

---

### 2. `require_role(role_name: str)` (Factory)
Creates a dependency that requires exactly one specific role.

```python
from app.dependencies import require_role

@router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    user = Depends(require_role("admin"))
):
    """Delete user - admin only."""
    return {"deleted": user_id}

@router.post("/support/tickets/{ticket_id}/resolve")
async def resolve_ticket(
    ticket_id: str,
    user = Depends(require_role("support_team"))
):
    """Resolve ticket - support team only."""
    return {"ticket": ticket_id, "resolved_by": user['email']}
```

**Behavior:**
- Authenticates user (401 if no token)
- Checks if user has required role
- Returns 403 with reason if role not found
- Returns user with `roles` field if authorized

**Error Response (403 Forbidden):**
```json
{
  "detail": "This endpoint requires 'admin' role. Your roles: ['support_team']"
}
```

---

### 3. `require_any_role(role_list: List[str])` (Factory)
Creates a dependency that requires at least ONE of the specified roles.

```python
from app.dependencies import require_any_role

@router.get("/dashboard/analytics")
async def analytics_dashboard(
    user = Depends(require_any_role(["admin", "moderator"]))
):
    """Dashboard - admin or moderator only."""
    return {"analytics": "data", "viewer": user['email']}

@router.post("/content/publish")
async def publish_content(
    content_id: str,
    user = Depends(require_any_role(["admin", "support_team", "moderator"]))
):
    """Publish content - any elevated role."""
    return {"published": content_id, "published_by": user['email']}
```

---

### 4. Using `require_role()` for Any Role

Simply pass the role name to `require_role()` - all roles work the same way:

```python
from app.dependencies import require_role

# Admin only
@router.delete("/admin/reset-db")
async def reset_database(user = Depends(require_role("admin"))):
    return {"status": "database reset"}

# Support team only
@router.post("/support/tickets")
async def create_ticket(user = Depends(require_role("support_team"))):
    return {"ticket_created": True}

# Moderator only
@router.post("/moderation/approve-comment/{comment_id}")
async def approve_comment(
    comment_id: str,
    user = Depends(require_role("moderator"))
):
    return {"comment_approved": comment_id}

# Custom role (added via .env)
@router.post("/content/publish")
async def publish_content(user = Depends(require_role("content_manager"))):
    return {"published": True}
```

**Benefits:**
- ✅ Single function for all roles
- ✅ No special imports needed for each role
- ✅ Add new roles without modifying code
- ✅ DRY principle (Don't Repeat Yourself)

---

## Usage Examples

### Example 1: Multi-Level Permissions

```python
from fastapi import APIRouter, Depends
from app.dependencies import require_role, require_any_role, get_current_user
from typing import Dict, Any

router = APIRouter(prefix="/api/v1/content", tags=["Content Management"])

# Anyone can view
@router.get("/articles")
async def list_articles():
    """Public endpoint."""
    return {"articles": []}

# Authenticated users can see drafts
@router.get("/drafts")
async def list_drafts(user: Dict[str, Any] = Depends(get_current_user)):
    """Authenticated users only."""
    return {"drafts": [], "viewer": user['email']}

# Authors or editors can create
@router.post("/articles")
async def create_article(
    user = Depends(require_any_role(["author", "editor"]))
):
    """Author or Editor only."""
    return {"created_by": user['email']}

# Only editors can publish
@router.post("/articles/{article_id}/publish")
async def publish_article(
    article_id: str,
    user = Depends(require_role("editor"))
):
    """Editor only."""
    return {"published": article_id}

# Only admins can delete
@router.delete("/articles/{article_id}")
async def delete_article(
    article_id: str,
    user = Depends(require_role("admin"))
):
    """Admin only."""
    return {"deleted": article_id}
```

### Example 2: Logging Who Did What

```python
import logging
from app.dependencies import require_role

logger = logging.getLogger(__name__)

@router.post("/admin/audit/clear-user-data/{user_id}")
async def clear_user_data(
    user_id: str,
    admin_user = Depends(require_role("admin"))
):
    """Clear user data - admin only with audit logging."""
    logger.warning(
        f"Admin {admin_user['email']} cleared data for user {user_id}"
    )
    return {"cleared": user_id, "by": admin_user['email']}
```

### Example 3: Custom Response Based on Role

```python
from typing import Dict, Any
from app.dependencies import get_current_user_with_roles

@router.get("/dashboard")
async def dashboard(user: Dict[str, Any] = Depends(get_current_user_with_roles)):
    """Dashboard with content based on user roles."""
    base_response = {
        "username": user['full_name'],
        "email": user['email'],
    }
    
    # Customize response based on roles
    if "admin" in user['roles']:
        base_response["widgets"] = ["analytics", "user_management", "system_settings"]
    elif "moderator" in user['roles']:
        base_response["widgets"] = ["content_review", "user_reports"]
    else:
        base_response["widgets"] = ["notifications", "my_profile"]
    
    return base_response
```

---

## Testing RBAC

### Test Endpoints

The backend includes test RBAC endpoints at `/api/v1/test-rbac/`:

- `GET /api/v1/test-rbac/public` - No auth required
- `GET /api/v1/test-rbac/authenticated` - Auth required
- `GET /api/v1/test-rbac/me-with-roles` - Auth + returns roles
- `GET /api/v1/test-rbac/admin-only` - Admin role required
- `GET /api/v1/test-rbac/support-only` - Support team role required
- `GET /api/v1/test-rbac/moderator-only` - Moderator role required
- `GET /api/v1/test-rbac/admin-or-moderator` - Admin OR Moderator
- `GET /api/v1/test-rbac/admin-or-support` - Admin OR Support Team
- `GET /api/v1/test-rbac/optional-with-roles` - Optional auth with role info

### Testing with cURL

```bash
# Get user roles (using valid token)
TOKEN="your_supabase_token"
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/test-rbac/me-with-roles

# Response:
# {
#   "user_id": "xxx",
#   "email": "admin@crackdsa.com",
#   "full_name": "Admin User",
#   "roles": ["admin"]
# }

# Try accessing admin endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/test-rbac/admin-only

# If user has admin role:
# {
#   "message": "Admin access granted",
#   "user_email": "admin@crackdsa.com",
#   "roles": ["admin"]
# }

# If user doesn't have admin role (403):
# {
#   "detail": "This endpoint requires 'admin' role. Your roles: ['support_team']"
# }
```

---

## Common Patterns

### Pattern 1: Admin Operations
```python
@router.post("/admin/settings")
async def update_settings(user = Depends(require_admin)):
    """Only admins can modify system settings."""
    return {"updated": True}
```

### Pattern 2: Multi-Role Endpoint
```python
@router.get("/reports")
async def access_reports(
    user = Depends(require_any_role(["admin", "analyst", "manager"]))
):
    """Admins, analysts, and managers can access reports."""
    return {"reports": []}
```

### Pattern 3: Role-Based Response Content
```python
@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    current_user = Depends(get_current_user_with_roles)
):
    """Show different data based on current user's role."""
    user_data = {"id": user_id, "email": "user@example.com"}
    
    # Admins see everything
    if "admin" in current_user['roles']:
        user_data["ip_history"] = []
        user_data["payment_history"] = []
    
    # Support can see contact info
    if "support_team" in current_user['roles']:
        user_data["phone"] = "xxx-xxx-xxxx"
    
    return user_data
```

### Pattern 4: Audit Logging
```python
import logging
from app.dependencies import require_role

logger = logging.getLogger(__name__)

@router.post("/admin/ban-user/{user_id}")
async def ban_user(
    user_id: str,
    admin = Depends(require_role("admin"))
):
    """Ban user - admin only with audit trail."""
    logger.critical(
        f"ADMIN_ACTION: {admin['email']} banned user {user_id}"
    )
    return {"banned": user_id}
```

---

## Error Handling

### 401 Unauthorized (Not Authenticated)
```json
{
  "detail": "No authentication token provided"
}
```

### 403 Forbidden (Authenticated but Insufficient Permissions)
```json
{
  "detail": "Not allowed to perform this action"
}
```

### Handling Errors in Frontend

```javascript
async function makeProtectedRequest(token, role) {
  const response = await fetch('/api/v1/admin/settings', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (response.status === 401) {
    // Not authenticated - redirect to login
    window.location.href = '/login';
  } else if (response.status === 403) {
    // Authenticated but insufficient permissions
    showError('You do not have permission to access this resource');
  } else if (response.ok) {
    // Success
    const data = await response.json();
    return data;
  }
}
```

---

## Security Considerations

1. **Email-Based Roles**: Roles are assigned by email address. Ensure email uniqueness and security in Supabase.

2. **Environment Variables**: Store role mappings in `.env` (never commit to git). Use appropriate secrets management in production.

3. **Role Verification**: Roles are verified on every request by checking the user's email against configured mappings.

4. **Audit Logging**: Log all admin/sensitive operations with the user who performed them.

5. **Least Privilege**: Assign the minimum necessary roles to each user.

6. **Role Granularity**: Design roles at appropriate granularity:
   - Not too broad (e.g., `user` is too vague)
   - Not too granular (e.g., `can_read_post_5` is too specific)

---

## Adding Custom Roles

### Step 1: Add to `.env`
```env
ROLE_CONTENT_MANAGER=cm1@crackdsa.com,cm2@crackdsa.com
```

### Step 2: Use in Routes
```python
from app.dependencies import require_role

@router.post("/content/publish")
async def publish_content(
    user = Depends(require_role("content_manager"))
):
    return {"published": True}
```

### Step 3: (Optional) Create Convenience Dependency

Add to `app/dependencies.py`:
```python
async def require_content_manager(
    user: Dict[str, Any] = Depends(require_role("content_manager"))
) -> Dict[str, Any]:
    """Dependency to require content_manager role."""
    return user
```

Then use in routes:
```python
from app.dependencies import require_content_manager

@router.post("/content/publish")
async def publish_content(user = Depends(require_content_manager)):
    return {"published": True}
```

---

## Production Checklist

- [ ] Define all required roles and assign emails
- [ ] Add role configuration to `.env` in production
- [ ] Update documentation with new roles
- [ ] Test each role-protected endpoint thoroughly
- [ ] Set up audit logging for sensitive operations
- [ ] Review role assignments regularly
- [ ] Use strong secrets management (Supabase, AWS Secrets, HashiCorp Vault)
- [ ] Monitor 403 errors for unauthorized access attempts

---

## Integration with Existing Code

### In New Routes
```python
from fastapi import APIRouter, Depends
from app.dependencies import require_role

router = APIRouter(prefix="/api/v1/feature", tags=["Feature"])

@router.get("/admin-dashboard")
async def admin_dashboard(user = Depends(require_role("admin"))):
    return {"data": "admin-only"}

app.include_router(router)
```

### Migrating Existing Routes

If you have existing protected routes:

**Before:**
```python
@router.post("/admin/actions")
async def admin_action(user = Depends(get_current_user)):
    # Manual role checking
    if user['email'] not in ["admin@crackdsa.com"]:
        raise HTTPException(status_code=403)
    return {"done": True}
```

**After:**
```python
@router.post("/admin/actions")
async def admin_action(user = Depends(require_admin)):
    # Automatic role checking, cleaner code
    return {"done": True}
```

---

## FAQ

**Q: Can a user have multiple roles?**
A: Yes! A user's email can appear in multiple `ROLE_*` variables, and they'll have all those roles.

**Q: Can I assign roles without restarting?**
A: Currently no - roles are loaded from env on startup. To add dynamic role assignment, you'd need to store roles in the database instead.

**Q: How do I remove a user's role?**
A: Remove their email from the corresponding `ROLE_*` environment variable and restart the app.

**Q: Can roles be hierarchical (admin > moderator > user)?**
A: Currently no - roles are flat. You can use `require_any_role(["admin", "moderator"])` to achieve similar behavior.

**Q: Should I use RBAC or OAuth scopes?**
A: Use RBAC for application-level permissions. OAuth scopes are for third-party integrations.
