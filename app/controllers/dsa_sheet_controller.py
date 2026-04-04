from typing import List
from fastapi import HTTPException
from app.schemas.dsa_sheet import DSASheet, DSASheetCreate, DSASheetUpdate
from app.services import dsa_sheet_service

async def list_sheets_handler(include_inactive: bool = False, token: str = None) -> List[dict]:
    """
    List sheets. Admin can see inactive ones.
    """
    try:
        return dsa_sheet_service.get_sheets(include_inactive=include_inactive, token=token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sheets: {str(e)}")

async def get_sheet_handler(sheet_id: str, include_inactive: bool = False, token: str = None) -> dict:
    """
    Get a single sheet by id. Admin can see inactive ones.
    """
    try:
        sheet = dsa_sheet_service.get_sheet_by_id(sheet_id, include_inactive=include_inactive, token=token)
        if not sheet:
            raise HTTPException(status_code=404, detail="Sheet not found")
        return sheet
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def create_sheet_handler(sheet_data: DSASheetCreate, token: str = None) -> dict:
    """
    Create a new sheet.
    """
    try:
        return dsa_sheet_service.create_sheet(sheet_data, token=token)
    except Exception as e:
        # Check for unique constraint violation from Supabase
        if "duplicate key" in str(e).lower():
            raise HTTPException(status_code=400, detail=f"Sheet with id {sheet_data.id} already exists")
        raise HTTPException(status_code=500, detail=str(e))

async def update_sheet_handler(sheet_id: str, update_data: DSASheetUpdate, token: str = None) -> dict:
    """
    Update a sheet fully.
    """
    try:
        return dsa_sheet_service.update_sheet(sheet_id, update_data, token=token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def delete_sheet_handler(sheet_id: str, token: str = None) -> dict:
    """
    Soft delete a sheet.
    """
    try:
        dsa_sheet_service.soft_delete_sheet(sheet_id, token=token)
        return {"message": "Sheet deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
