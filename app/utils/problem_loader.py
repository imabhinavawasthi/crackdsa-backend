import json
from pathlib import Path
from typing import List, Dict, Any

DATA_DIR = Path(__file__).parent.parent.parent / "data"
PROBLEMS_FILE = DATA_DIR / "problems.json"

def load_all_problems() -> List[Dict[str, Any]]:
    """Load the full problems dataset from JSON."""
    if not PROBLEMS_FILE.exists():
        return []
    with open(PROBLEMS_FILE, "r") as f:
        return json.load(f)

def get_problems_by_topics(topics: List[str]) -> List[Dict[str, Any]]:
    """Filter problems that match the specific topic strings."""
    all_problems = load_all_problems()
    if not topics:
        return all_problems
    return [p for p in all_problems if p.get("topic") in topics]

def get_relevant_problems_for_ai(strong_topics: List[str], weak_topics: List[str]) -> List[Dict[str, Any]]:
    """
    Returns a subset of problems most relevant to the user to avoid exceeding the LLM context window.
    For MVP, we just return the full list if it's small enough, otherwise prioritize weak topics.
    """
    all_problems = load_all_problems()
    
    # In MVP, our dataset is small so we can return all. 
    # Scalable version: pick N random/easy from strong topics, M from weak topics.
    return all_problems
