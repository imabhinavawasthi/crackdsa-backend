from typing import Optional
from datetime import date
from app.database import get_supabase_client
import logging

logger = logging.getLogger(__name__)


def get_problem_of_the_day() -> Optional[dict]:
    """
    Returns a single practice problem for today using a deterministic
    date-seed algorithm.

    Algorithm:
        1. Count total active problems.
        2. seed = YYYY * 10000 + MM * 100 + DD
        3. offset = seed % total_count
        4. Fetch one problem at that offset (ordered by created_at ASC).
    """
    client = get_supabase_client()

    # 1. Count total active problems
    count_resp = (
        client.table("practice_problems")
        .select("id", count="exact")
        .eq("is_active", True)
        .limit(0)
        .execute()
    )
    total_count = count_resp.count
    if not total_count or total_count == 0:
        logger.warning("POTD: No active practice problems found.")
        return None

    # 2. Compute deterministic offset from today's date
    today = date.today()
    seed = today.year * 10000 + today.month * 100 + today.day
    offset = seed % total_count

    # 3. Fetch the problem at that offset
    cols = "id,slug,title,difficulty,platform,problem_url"
    resp = (
        client.table("practice_problems")
        .select(cols)
        .eq("is_active", True)
        .order("created_at", desc=False)
        .range(offset, offset)
        .execute()
    )

    if resp.data:
        return resp.data[0]

    # Fallback: return the first problem if offset somehow misses
    logger.warning(f"POTD: Offset {offset} returned no data, falling back to first problem.")
    fallback = (
        client.table("practice_problems")
        .select(cols)
        .eq("is_active", True)
        .order("created_at", desc=False)
        .limit(1)
        .execute()
    )
    return fallback.data[0] if fallback.data else None
