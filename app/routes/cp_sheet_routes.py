from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from app.database import get_supabase_client
from app.dependencies import get_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/cp",
    tags=["Competitive Programming Sheets"]
)

@router.get("/newbie-to-expert")
def get_newbie_to_expert_sheet(token: Optional[str] = Depends(get_token)) -> Dict[str, Any]:
    """
    Fetch the Newbie to Expert CP Sheet directly from the expert_sheet table.
    """
    try:
        client = get_supabase_client(jwt_token=token)
        res = client.table("expert_sheet").select("*").order("difficulty", desc=False).execute()
        rows = res.data or []
        
        sheet_title = rows[0].get("sheet_title") if rows else "Newbie to Expert CP Sheet"
        sheet_desc = (
            rows[0].get("sheet_description")
            if rows
            else "Hand Picked CP Problems with Video Editorials & Code Solutions"
        )
        
        return {
            "sheet_id": "newbie-to-expert",
            "title": sheet_title,
            "description": sheet_desc,
            "total_problems": len(rows),
            "problems": rows,
        }
    except Exception as e:
        logger.error(f"Error fetching newbie-to-expert CP sheet: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load CP sheet")
