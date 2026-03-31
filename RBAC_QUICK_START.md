# RBAC Quick Start Guide

Get RBAC working in 5 minutes!

---

## Step 1: Configure Roles in `.env`

Add these lines to your `.env` file:

```env
# Role-Based Access Control
ROLE_ADMIN=admin@crackdsa.com,admin2@crackdsa.com
ROLE_SUPPORT_TEAM=support@crackdsa.com
ROLE_MODERATOR=moderator@crackdsa.com
```

Replace `admin@crackdsa.com` with your actual email address you use in Supabase.

---

## Step 2: Restart the Server

```bash
# Kill existing server (Ctrl+C)
# Then restart:
cd /Users/abhinavawasthi/Desktop/crackdsa-rebuild/backend
python3 -m uvicorn app.main:app --reload
```

---

## Step 3: Get Your Supabase Token

### Option A: Use Supabase Dashboard
1. Go to Supabase dashboard
2. Create a test user or use your own account
3. In Supabase Auth, find the user and copy the access token
4. Or just sign in to your app normally and grab the token

### Option B: Use Browser DevTools
1. Visit `http://localhost:3000` (your frontend)
2. Sign in with Google
3. Open DevTools → Application → Cookies
4. Find cookie named `supabase_token`
5. Copy the value

---

## Step 4: Test RBAC Endpoints

### Get Your Roles
```bash
TOKEN="paste_your_token_here"

curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/test-rbac/me-with-roles | python3 -m json.tool
```

Expected response (if you're admin@crackdsa.com):
```json
{
  "user_id": "xxx",
  "email": "admin@crackdsa.com",
  "full_name": "Your Name",
  "roles": ["admin"]
}
```

### Test Admin-Only Endpoint
```bash
TOKEN="paste_your_token_here"

# If your email is in ROLE_ADMIN, this works:
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/test-rbac/admin-only | python3 -m json.tool
```

Response if authorized:
```json
{
  "message": "Admin access granted",
  "user_email": "admin@crackdsa.com",
  "roles": ["admin"]
}
```

Response if NOT authorized (403):
```json
{
  "detail": "This endpoint requires 'admin' role. Your roles: []"
}
```

---

## Step 5: Test All Endpoints

Visit the interactive API docs:
- **http://localhost:8000/docs**

All RBAC test endpoints are under **`/api/v1/test-rbac/`**:

1. **public** - No auth needed ✓
2. **authenticated** - Any authenticated user
3. **me-with-roles** - See your roles
4. **admin-only** - Requires admin role
5. **support-only** - Requires support_team role
6. **moderator-only** - Requires moderator role
7. **admin-or-moderator** - Admin OR moderator
8. **admin-or-support** - Admin OR support team
9. **optional-with-roles** - Works with or without auth

Try each one with your token!

---

## Using RBAC in Your Own Routes

### Protect an Endpoint (Admin Only)
```python
from fastapi import APIRouter, Depends
from app.dependencies import require_role

router = APIRouter()

@router.post("/admin/delete-user/{user_id}")
async def delete_user(user_id: str, user = Depends(require_role("admin"))):
    """Only admins can delete users."""
    return {"deleted": user_id, "by": user['email']}

# Register in main.py:
# app.include_router(router, prefix="/api/v1")
```

### Protect with Multiple Roles
```python
from app.dependencies import require_any_role

@router.get("/dashboard")
async def dashboard(user = Depends(require_any_role(["admin", "moderator"]))):
    """Admin or Moderator can view."""
    return {"dashboard": "data"}
```

### Support Team Only
```python
@router.get("/support/tickets")
async def list_tickets(user = Depends(require_role("support_team"))):
    """Support team access only."""
    return {"tickets": []}
```

### Custom Role
```python
@router.post("/content/approve")
async def approve_content(user = Depends(require_role("content_manager"))):
    """Content manager approval only."""
    return {"approved": True}
```

---

## Common Patterns

### Pattern 1: Admin Dashboard
```python
@router.get("/admin/dashboard")
async def admin_dashboard(user = Depends(require_role("admin"))):
    return {"stats": "admin-only-data"}
```

### Pattern 2: Multiple Role Endpoint
```python
@router.post("/moderation/approve")
async def approve_content(user = Depends(require_any_role(["admin", "moderator"]))):
    return {"approved": True}
```

### Pattern 3: Role-Based Logic
```python
@router.get("/content")
async def get_content(user = Depends(get_current_user_with_roles)):
    content = list_public_content()
    
    if "admin" in user['roles']:
        content.extend(list_admin_content())
    
    if "moderator" in user['roles']:
        content.extend(list_flagged_content())
    
    return {"content": content}
```

---

## Troubleshooting

### "No authentication token provided" (401)
- **Problem**: You didn't include a token
- **Solution**: Add the `-H "Authorization: Bearer <TOKEN>"` header

### "This endpoint requires 'admin' role" (403)
- **Problem**: Your email isn't in `ROLE_ADMIN` in `.env`
- **Solution**: 
  1. Check what roles you have: `curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/test-rbac/me-with-roles`
  2. Add your email to the appropriate role in `.env`
  3. Restart the server

### Token expired (401)
- **Solution**: Get a fresh token and try again

### Role changes not taking effect
- **Problem**: Server cached the old config
- **Solution**: Restart the server after editing `.env`

---

## Adding a New Role

### Example: Add "CONTENT_MANAGER" Role

1. **Edit `.env`:**
   ```env
   ROLE_CONTENT_MANAGER=cm@crackdsa.com
   ```

2. **Restart server** (Ctrl+C, then run again)

3. **Use in routes:**
   ```python
   @router.post("/content/approve")
   async def approve_content(user = Depends(require_role("content_manager"))):
       return {"approved": True}
   ```

That's it! 🎉

---

## Testing Checklist

- [ ] Added roles to `.env`
- [ ] Restarted server
- [ ] Got a valid Supabase token
- [ ] Tested `/test-rbac/me-with-roles` (see your roles)
- [ ] Tested `/test-rbac/admin-only` (or your role)
- [ ] Tested `/test-rbac/admin-or-moderator` (multiple roles)
- [ ] Tried accessing unauthorized endpoint (got 403)
- [ ] Created custom role in `.env`
- [ ] Used new role with `require_role("role_name")`
- [ ] All tests passed ✅

---

## Next Steps

1. **Read full RBAC guide**: [docs/RBAC.md](docs/RBAC.md)
2. **Add RBAC to existing endpoints**: Replace `get_current_user` with `require_admin`, etc.
3. **Add custom roles** as your app grows
4. **Review security**: Check [docs/RBAC.md - Security Considerations](docs/RBAC.md#security-considerations)

---

## Quick Reference

| Need | Use |
|------|-----|
| Check auth only | `Depends(get_current_user)` |
| Check auth + return roles | `Depends(get_current_user_with_roles)` |
| Require admin role | `Depends(require_role("admin"))` |
| Require support team | `Depends(require_role("support_team"))` |
| Require moderator | `Depends(require_role("moderator"))` |
| Require custom role | `Depends(require_role("custom_role"))` |
| Require multiple roles | `Depends(require_any_role(["role1", "role2"]))` |
| Optional auth | `Depends(get_current_user_optional)` |

---

## Need Help?

- **RBAC Configuration**: See [docs/RBAC.md - Configuration](docs/RBAC.md#configuration)
- **Usage Examples**: See [docs/RBAC.md - Usage Examples](docs/RBAC.md#usage-examples)
- **Security**: See [docs/RBAC.md - Security Considerations](docs/RBAC.md#security-considerations)
- **Troubleshooting**: See [docs/RBAC.md - Error Handling](docs/RBAC.md#error-handling)

---

## Files Reference

- **Implementation Summary**: [RBAC_IMPLEMENTATION.md](RBAC_IMPLEMENTATION.md)
- **Full Documentation**: [docs/RBAC.md](docs/RBAC.md)
- **Config Template**: [.env.example](.env.example)
- **Test Routes**: [app/routes/test_rbac_routes.py](app/routes/test_rbac_routes.py)
- **Dependencies**: [app/dependencies.py](app/dependencies.py)
- **Config**: [app/config.py](app/config.py)

---

✅ **Ready to implement RBAC!** Start with Step 1 above.
