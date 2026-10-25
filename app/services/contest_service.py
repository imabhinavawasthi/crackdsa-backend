import re
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.database import get_supabase_client
from app.utils.cache import cache_manager

def slugify(text: str) -> str:
    """Create a URL-safe slug from a string."""
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')

def map_difficulty(diff: Optional[int], platform: str = "") -> str:
    """Map integer difficulty to Easy, Medium, or Hard based on platform standards."""
    if diff is None:
        return "Medium"
    p = platform.lower()
    
    # LeetCode: 0 -> Easy, 1 -> Medium, 2+ -> Hard
    if "leetcode" in p:
        if diff <= 0:
            return "Easy"
        elif diff == 1:
            return "Medium"
        else:
            return "Hard"
            
    # Rating-based difficulty (Codeforces ratings like 800-2400)
    if diff >= 500:
        if diff < 1200:
            return "Easy"
        elif diff < 1600:
            return "Medium"
        else:
            return "Hard"
            
    # Tier-based difficulty for Codeforces / CodeChef (0, 1 = Easy; 2 = Medium; 3, 4 = Hard)
    if diff <= 1:
        return "Easy"
    elif diff == 2:
        return "Medium"
    else:
        return "Hard"

def extract_problem_index(name: str, fallback_index: int) -> Optional[str]:
    """Avoid assigning word prefixes or artificial sequences to problems."""
    return None

def infer_contest_url(platform: str, contest: str, problems: List[Dict[str, Any]]) -> Optional[str]:
    """Infer the main official contest URL from problems links."""
    for p in problems:
        link = p.get("problem_link") or ""
        if "codeforces.com/contest/" in link:
            match = re.search(r'codeforces\.com/contest/(\d+)', link)
            if match:
                return f"https://codeforces.com/contest/{match.group(1)}"
        elif "leetcode.com/contest/" in link:
            match = re.search(r'leetcode\.com/contest/([^/]+)', link)
            if match:
                return f"https://leetcode.com/contest/{match.group(1)}/"
        elif "codechef.com/" in link:
            match = re.search(r'codechef\.com/([^/]+)', link)
            if match:
                return f"https://www.codechef.com/{match.group(1)}"
        elif link:
            return link
    return None

def format_date_str(iso_date: Optional[str]) -> str:
    if not iso_date:
        return ""
    try:
        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y")
    except Exception:
        return iso_date[:10] if len(iso_date) >= 10 else iso_date

def format_platform_name(p: str) -> str:
    p_lower = p.lower()
    if p_lower == "codeforces":
        return "Codeforces"
    if p_lower == "leetcode":
        return "LeetCode"
    if p_lower == "codechef":
        return "CodeChef"
    if p_lower == "atcoder":
        return "AtCoder"
    return p.capitalize()

def get_contests_paginated(
    platform: Optional[str] = None, 
    search: Optional[str] = None,
    sort_by: Optional[str] = "latest",
    limit: int = 10,
    page: int = 1,
    token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch contest summaries with complete pagination metadata and aggregated platform statistics.
    """
    cache_key = f"contest_paginated:{platform}:{search}:{sort_by}:{limit}:{page}"
    cached_val = cache_manager.get(cache_key)
    if cached_val is not None:
        return cached_val

    client = get_supabase_client(jwt_token=token)
    select_fields = "contest, platform, created_at, difficulty, video_editorial"
    query = client.table("contest_editorials").select(select_fields)
    response = query.order("created_at", desc=True).execute()
    rows = response.data or []

    grouped: Dict[str, Dict[str, Any]] = {}
    platform_counts: Dict[str, int] = {}
    total_problems = len(rows)

    for row in rows:
        c_name = (row.get("contest") or "General Contest").strip()
        p_name = (row.get("platform") or "other").lower().strip()
        key = f"{p_name}::{c_name}"
        
        diff = row.get("difficulty")
        diff_label = map_difficulty(diff, p_name)
        has_vid = bool(row.get("video_editorial"))
        
        if key not in grouped:
            c_slug = slugify(c_name)
            grouped[key] = {
                "id": f"{p_name}-{c_slug}",
                "platform": p_name,
                "contest": c_name,
                "created_at": row.get("created_at") or "",
                "total_problems": 0,
                "easy_count": 0,
                "medium_count": 0,
                "hard_count": 0,
                "has_video": False,
                "badge": None,
            }
            platform_counts[p_name] = platform_counts.get(p_name, 0) + 1
            
        group = grouped[key]
        group["total_problems"] += 1
        if diff_label == "Easy":
            group["easy_count"] += 1
        elif diff_label == "Medium":
            group["medium_count"] += 1
        else:
            group["hard_count"] += 1
            
        if has_vid:
            group["has_video"] = True

    all_contests = list(grouped.values())
    total_contests = len(all_contests)

    # Format date and assign badge to top recent items
    for idx, item in enumerate(all_contests):
        item["date"] = format_date_str(item.get("created_at"))
        if idx == 0:
            item["badge"] = "HOT"
        elif idx in [1, 2]:
            item["badge"] = "NEW"

    platforms_list = [
        {"id": "all", "label": "All Contests", "count": total_contests}
    ]
    for p, cnt in sorted(platform_counts.items(), key=lambda x: -x[1]):
        platforms_list.append({
            "id": p,
            "label": format_platform_name(p),
            "count": cnt
        })

    # Filter by platform
    filtered = all_contests
    if platform and platform.lower() != "all":
        p_clean = platform.lower().strip()
        filtered = [c for c in filtered if p_clean in c["platform"].lower()]

    # Filter by search
    if search and search.strip():
        s = search.lower().strip()
        filtered = [
            c for c in filtered 
            if s in c["contest"].lower() or s in c["platform"].lower()
        ]

    # Sort
    if sort_by == "oldest":
        filtered.sort(key=lambda x: x.get("created_at") or "")
    elif sort_by == "problems":
        filtered.sort(key=lambda x: x.get("total_problems", 0), reverse=True)
    else:  # "latest"
        filtered.sort(key=lambda x: x.get("created_at") or "", reverse=True)

    total_count = len(filtered)
    limit = max(1, limit or 10)
    current_page = max(1, page or 1)
    total_pages = max(1, (total_count + limit - 1) // limit) if total_count > 0 else 1

    start_idx = (current_page - 1) * limit
    end_idx = start_idx + limit
    items = filtered[start_idx:end_idx]

    result = {
        "items": items,
        "total_count": total_count,
        "total_pages": total_pages,
        "page": current_page,
        "limit": limit,
        "total_contests": total_contests,
        "total_problems": total_problems,
        "platforms": platforms_list,
    }
    cache_manager.set(cache_key, result, ttl=86400, namespace="contests")
    return result

def get_contests(
    platform: Optional[str] = None, 
    search: Optional[str] = None,
    sort_by: Optional[str] = "latest",
    limit: Optional[int] = None,
    page: Optional[int] = 1,
    token: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch contest summaries grouped by (platform, contest).
    Maintains backward compatibility for direct list queries.
    """
    effective_limit = limit if limit is not None else 10000
    res = get_contests_paginated(
        platform=platform,
        search=search,
        sort_by=sort_by,
        limit=effective_limit,
        page=page or 1,
        token=token
    )
    return res["items"]

def get_contest_detail(platform: str, contest_slug: str, token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch a single contest with all its detailed problems and editorials.
    """
    cache_key = f"contest_detail:{platform.lower().strip()}:{contest_slug.lower().strip()}"
    cached_val = cache_manager.get(cache_key)
    if cached_val is not None:
        return cached_val

    client = get_supabase_client(jwt_token=token)
    p_clean = platform.lower().strip()
    
    # Query all problems for this platform
    query = client.table("contest_editorials").select("*").ilike("platform", p_clean)
    response = query.order("created_at", desc=False).execute()
    rows = response.data or []
    
    # Match the contest by slug or exact name
    matched_rows = []
    contest_name = ""
    for r in rows:
        c = (r.get("contest") or "").strip()
        if slugify(c) == contest_slug or slugify(f"{p_clean}-{slugify(c)}") == contest_slug or c.lower() == contest_slug.lower():
            matched_rows.append(r)
            if not contest_name:
                contest_name = c
                
    if not matched_rows:
        return None
        
    enhanced_problems = []
    for idx, prob in enumerate(matched_rows):
        diff = prob.get("difficulty")
        p_index = extract_problem_index(prob.get("problem_name", ""), idx)
        has_editorial = bool(prob.get("video_editorial") or prob.get("editorial") or prob.get("solution_link"))
        
        # Clean topic tags
        raw_tags = prob.get("topic_tags")
        clean_tags = []
        if isinstance(raw_tags, list):
            for t in raw_tags:
                if isinstance(t, dict):
                    clean_tags.append(t.get("label") or t.get("value") or "")
                elif isinstance(t, str):
                    clean_tags.append(t)
        elif isinstance(raw_tags, dict):
            clean_tags = raw_tags.get("tags") or []
        prob["topic_tags"] = [t for t in clean_tags if t]
        
        prob["problem_index"] = p_index
        prob["difficulty_label"] = map_difficulty(diff, p_clean)
        prob["has_editorial"] = has_editorial
        enhanced_problems.append(prob)
        
    # Sort problems in ascending order of created_at (natural contest order)
    enhanced_problems.sort(key=lambda p: p.get("created_at") or "")
    
    first_date = matched_rows[0].get("created_at") if matched_rows else ""
    contest_url = infer_contest_url(p_clean, contest_name, matched_rows)
    
    result = {
        "id": f"{p_clean}-{slugify(contest_name)}",
        "platform": p_clean,
        "contest": contest_name,
        "date": format_date_str(first_date),
        "total_problems": len(enhanced_problems),
        "contest_url": contest_url,
        "problems": enhanced_problems,
    }
    cache_manager.set(cache_key, result, ttl=86400, namespace="contests")
    return result

def get_problem_editorial(
    platform: str, 
    contest_slug: str, 
    problem_slug: str, 
    token: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Fetch a single contest problem editorial with sibling problem references.
    """
    cache_key = f"contest_editorial:{platform.lower().strip()}:{contest_slug.lower().strip()}:{problem_slug.lower().strip()}"
    cached_val = cache_manager.get(cache_key)
    if cached_val is not None:
        return cached_val

    contest_data = get_contest_detail(platform, contest_slug, token=token)
    if not contest_data:
        return None
        
    problems = contest_data["problems"]
    target_problem = None
    target_index = -1
    
    for idx, p in enumerate(problems):
        if p.get("slug_url") == problem_slug or str(p.get("id")) == problem_slug or slugify(p.get("problem_name", "")) == problem_slug:
            target_problem = p
            target_index = idx
            break
            
    if not target_problem:
        return None
        
    prev_problem = problems[target_index - 1] if target_index > 0 else None
    next_problem = problems[target_index + 1] if target_index < len(problems) - 1 else None
    
    # Create lightweight sibling list for navigation
    siblings = [
        {
            "id": p["id"],
            "slug_url": p["slug_url"],
            "problem_name": p["problem_name"],
            "problem_index": p["problem_index"],
            "difficulty_label": p["difficulty_label"],
            "has_editorial": p["has_editorial"]
        }
        for p in problems
    ]
    
    result = {
        "contest": {
            "id": contest_data["id"],
            "platform": contest_data["platform"],
            "contest": contest_data["contest"],
            "date": contest_data["date"],
            "contest_url": contest_data["contest_url"]
        },
        "problem": target_problem,
        "prev_problem": {
            "slug_url": prev_problem["slug_url"],
            "problem_name": prev_problem["problem_name"],
            "problem_index": prev_problem["problem_index"]
        } if prev_problem else None,
        "next_problem": {
            "slug_url": next_problem["slug_url"],
            "problem_name": next_problem["problem_name"],
            "problem_index": next_problem["problem_index"]
        } if next_problem else None,
        "siblings": siblings
    }
    cache_manager.set(cache_key, result, ttl=86400, namespace="contests")
    return result
