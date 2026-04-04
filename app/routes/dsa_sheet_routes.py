from typing import List, Optional
from fastapi import APIRouter, Depends
from app.schemas.dsa_sheet import DSASheet, DSASheetCreate, DSASheetUpdate
from app.controllers import dsa_sheet_controller
from app.dependencies import require_role_with_token, get_token

# --- Public Router ---
# For general users, only GET active sheets
public_router = APIRouter(
    prefix="/dsa-sheets",
    tags=["DSA Sheets (Public)"]
)

@public_router.get("", response_model=List[DSASheet])
async def list_sheets_public(token: Optional[str] = Depends(get_token)):
    """
    List all active sheets for public users.
    Enforces RLS if token is present.
    """
    return await dsa_sheet_controller.list_sheets_handler(include_inactive=False, token=token)

@public_router.get("/{id}", response_model=DSASheet)
async def get_sheet_public(id: str, token: Optional[str] = Depends(get_token)):
    """
    Get a single active sheet by id.
    """
    return await dsa_sheet_controller.get_sheet_handler(id, include_inactive=False, token=token)


# --- Admin Router ---
# Full CRUD, requires admin role, includes inactive sheets
admin_router = APIRouter(
    prefix="/admin/dsa-sheets",
    tags=["DSA Sheets (Admin)"]
    # We apply the dependency at each route to extract the token easily
)

@admin_router.get("", response_model=List[DSASheet])
async def list_sheets_admin(auth_data: dict = Depends(require_role_with_token("admin"))):
    """
    List all sheets (active + inactive) for administrative use.
    Requires 'admin' role.
    """
    return await dsa_sheet_controller.list_sheets_handler(include_inactive=True, token=auth_data["token"])

@admin_router.get("/{id}", response_model=DSASheet)
async def get_sheet_admin(id: str, auth_data: dict = Depends(require_role_with_token("admin"))):
    """
    Get any sheet by id (even if inactive).
    Requires 'admin' role.
    """
    return await dsa_sheet_controller.get_sheet_handler(id, include_inactive=True, token=auth_data["token"])

@admin_router.post("", response_model=DSASheet)
async def create_sheet_admin(sheet_data: DSASheetCreate, auth_data: dict = Depends(require_role_with_token("admin"))):
    """
    Create a new sheet.
    Requires 'admin' role.
    """
    return await dsa_sheet_controller.create_sheet_handler(sheet_data, token=auth_data["token"])

@admin_router.put("/{id}", response_model=DSASheet)
async def update_sheet_admin(id: str, update_data: DSASheetUpdate, auth_data: dict = Depends(require_role_with_token("admin"))):
    """
    Update an existing sheet fully.
    Requires 'admin' role.
    """
    return await dsa_sheet_controller.update_sheet_handler(id, update_data, token=auth_data["token"])

@admin_router.delete("/{id}")
async def delete_sheet_admin(id: str, auth_data: dict = Depends(require_role_with_token("admin"))):
    """
    Soft delete a sheet.
    Requires 'admin' role.
    """
    return await dsa_sheet_controller.delete_sheet_handler(id, token=auth_data["token"])
