from fastapi import APIRouter, HTTPException, Depends, status
from uuid import UUID
from app.dependencies import get_current_user, get_current_user_with_token
from app.schemas.user_asset_state import (
    UserAssetStateResponseSchema,
    UserAssetStateUpdateSchema,
    AssetTypeEnum,
)
from app.services.user_asset_state_service import UserAssetStateService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/user/assets/states",
    tags=["User Asset Progress & Notepad"]
)

@router.get("", response_model=list[UserAssetStateResponseSchema])
@router.get("/", response_model=list[UserAssetStateResponseSchema], include_in_schema=False)
def list_user_asset_states(auth_data = Depends(get_current_user_with_token)):
    """
    Fetch all learning asset completion states, bookmarks, and notepad notes 
    for the currently logged-in user in a single bulk database query!
    """
    current_user = auth_data["user"]
    token = auth_data["token"]
    try:
        user_uuid = UUID(current_user["id"])
        return UserAssetStateService.get_user_asset_states(user_uuid, token)
    except Exception as e:
        logger.error(f"Error fetching asset states for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user asset states"
        )

@router.post("/{asset_type}/{asset_id}", response_model=UserAssetStateResponseSchema)
@router.post("/{asset_type}/{asset_id}/", response_model=UserAssetStateResponseSchema, include_in_schema=False)
def update_user_asset_state(
    asset_type: AssetTypeEnum,
    asset_id: str,
    data: UserAssetStateUpdateSchema,
    auth_data = Depends(get_current_user_with_token),
):
    """
    Upsert (insert or merge-update) the learning status, bookmark state, or notepad entries 
    for a specific asset (video, problem, or article). 
    Merges updates with existing states safely to avoid accidental data loss.
    """
    current_user = auth_data["user"]
    token = auth_data["token"]
    try:
        user_uuid = UUID(current_user["id"])
        return UserAssetStateService.upsert_user_asset_state(
            user_id=user_uuid,
            asset_id=asset_id,
            asset_type=asset_type.value,
            data=data,
            token=token
        )
    except Exception as e:
        logger.error(f"Error updating asset state for user {current_user['id']} on asset {asset_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update asset state: {str(e)}"
        )
