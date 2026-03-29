from app.models.user_preferences import UserPreferences

def validate_preferences(prefs: UserPreferences) -> bool:
    """
    Additional validation for preferences that Pydantic alone might not catch,
    like complex cross-field dependencies.
    For MVP, Pydantic's annotations handle `timeline_days` >= 30 and `weekly_hours` >= 5.
    """
    
    # Ensure there are no overlapping topics in strong vs weak.
    overlap = set(prefs.strong_topics).intersection(set(prefs.weak_topics))
    if overlap:
        raise ValueError(f"Topics cannot be both strong and weak: {overlap}")
        
    return True
