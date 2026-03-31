"""Test routes package."""

from app.routes.test_routes.auth import router as auth_router
from app.routes.test_routes.rbac import router as rbac_router

__all__ = ["auth_router", "rbac_router"]
