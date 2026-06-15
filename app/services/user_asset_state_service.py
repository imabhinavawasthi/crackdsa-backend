from app.database import get_supabase_client
from app.schemas.user_asset_state import (
    UserAssetStateResponseSchema,
    UserAssetStateUpdateSchema,
    AssetStatusEnum,
)
from uuid import UUID
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class UserAssetStateService:
    """Service layer for User Asset States (Completion, Bookmarks, and Notes)"""

    TABLE_NAME = "user_asset_states"

    @staticmethod
    def get_user_asset_states(user_id: UUID, token: str) -> list[UserAssetStateResponseSchema]:
        """Fetch all learning interactions, bookmarks, and notepad entries for a user in a single bulk query"""
        try:
            client = get_supabase_client(token)
            
            response = client.table(UserAssetStateService.TABLE_NAME).select(
                "*"
            ).eq(
                "user_id", str(user_id)
            ).execute()
            
            states = []
            for item in response.data or []:
                states.append(UserAssetStateResponseSchema(**item))
                
            logger.info(f"Fetched {len(states)} asset state rows for user {user_id} in a single call")
            return states
        except Exception as e:
            logger.error(f"Error fetching asset states for user {user_id}: {str(e)}")
            raise

    @staticmethod
    def upsert_user_asset_state(
        user_id: UUID, 
        asset_id: str, 
        asset_type: str, 
        data: UserAssetStateUpdateSchema,
        token: str
    ) -> UserAssetStateResponseSchema:
        """
        Upsert (insert or merge-update) the state, notes, or bookmark of an individual asset for a user.
        Merges with existing states in the database to prevent accidental data loss!
        """
        try:
            client = get_supabase_client(token)
            user_uuid_str = str(user_id)

            # 1. Fetch existing state to perform a safe merge
            response = client.table(UserAssetStateService.TABLE_NAME).select(
                "*"
            ).eq(
                "user_id", user_uuid_str
            ).eq(
                "asset_id", asset_id
            ).eq(
                "asset_type", asset_type
            ).execute()

            existing_row = response.data[0] if response.data and len(response.data) > 0 else None

            # 2. Build payload by merging new changes over existing values
            payload = {
                "user_id": user_uuid_str,
                "asset_id": asset_id,
                "asset_type": asset_type,
                "updated_at": datetime.utcnow().isoformat(),
            }

            if existing_row:
                # Merge notes
                if data.notes is not None:
                    payload["notes"] = [note.dict() for note in data.notes]
                else:
                    payload["notes"] = existing_row.get("notes") or []

                # Merge bookmark flag
                if data.is_bookmarked is not None:
                    payload["is_bookmarked"] = data.is_bookmarked
                    if data.is_bookmarked and not existing_row.get("is_bookmarked"):
                        payload["bookmarked_at"] = datetime.utcnow().isoformat()
                    elif not data.is_bookmarked:
                        payload["bookmarked_at"] = None
                else:
                    payload["is_bookmarked"] = existing_row.get("is_bookmarked", False)
                    payload["bookmarked_at"] = existing_row.get("bookmarked_at")

                # Merge learning status
                if data.status is not None:
                    payload["status"] = data.status.value
                else:
                    payload["status"] = existing_row.get("status", "pending")

                # Merge metadata bucket
                if data.metadata is not None:
                    # Shallow merge metadata objects
                    current_meta = existing_row.get("metadata") or {}
                    current_meta.update(data.metadata)
                    payload["metadata"] = current_meta
                else:
                    payload["metadata"] = existing_row.get("metadata") or {}
                    
                payload["id"] = existing_row["id"]
                payload["last_interacted_at"] = datetime.utcnow().isoformat()
            else:
                # Initialize a brand-new row
                payload["notes"] = [note.dict() for note in data.notes] if data.notes is not None else []
                payload["is_bookmarked"] = data.is_bookmarked if data.is_bookmarked is not None else False
                payload["bookmarked_at"] = datetime.utcnow().isoformat() if payload["is_bookmarked"] else None
                payload["status"] = data.status.value if data.status is not None else "pending"
                payload["metadata"] = data.metadata or {}
                payload["last_interacted_at"] = datetime.utcnow().isoformat()

            # 3. Fire upsert to Supabase
            upsert_res = client.table(UserAssetStateService.TABLE_NAME).upsert(payload).execute()

            if not upsert_res.data or len(upsert_res.data) == 0:
                raise Exception("Failed to upsert asset state: No data returned from database")

            updated_row = upsert_res.data[0]
            logger.info(f"Upserted asset state {updated_row['id']} for user {user_id} on asset {asset_id}")
            return UserAssetStateResponseSchema(**updated_row)

        except Exception as e:
            logger.error(f"Error upserting asset state for user {user_id} on asset {asset_id}: {str(e)}")
            raise
