"""Load DSA problems from JSON data."""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"
PROBLEMS_FILE = DATA_DIR / "problems.json"


def load_all_problems() -> List[Dict[str, Any]]:
    """Load the full problems dataset from JSON."""
    try:
        if not PROBLEMS_FILE.exists():
            logger.error(f"Problems file not found: {PROBLEMS_FILE}")
            return []
        
        with open(PROBLEMS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse problems JSON: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error loading problems: {e}")
        return []


def get_problems_by_topics(topics: List[str]) -> List[Dict[str, Any]]:
    """Filter problems that match the specific topic strings."""
    all_problems = load_all_problems()
    if not all_problems:
        return []
    if not topics:
        return all_problems
    return [p for p in all_problems if p.get("topic") in topics]


def get_relevant_problems_for_ai(strong_topics: List[str], weak_topics: List[str]) -> List[Dict[str, Any]]:
    """
    Returns a subset of problems most relevant to the user to avoid exceeding the LLM context window.
    For MVP, we just return the full list if it's small enough.
    """
    return load_all_problems()
