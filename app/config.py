"""Application configuration from environment variables."""

from pydantic_settings import BaseSettings
from typing import Dict, List


class Settings(BaseSettings):
    """Application settings."""
    
    # Supabase Configuration
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    
    # AI Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # RBAC Configuration (comma-separated emails per role)
    # Example: ROLE_ADMIN=a@crackdsa.com,b@crackdsa.com
    ROLE_ADMIN: str = ""
    ROLE_SUPPORT_TEAM: str = ""
    ROLE_MODERATOR: str = ""
    
    class Config:
        env_file = ".env"
        extra = "ignore"
    
    @property
    def role_mapping(self) -> Dict[str, List[str]]:
        """Parse role configuration into a mapping of role -> list of emails."""
        mapping = {}
        
        # Dynamically get all ROLE_ fields
        for field_name in self.model_fields.keys():
            if field_name.startswith("ROLE_"):
                role_name = field_name[5:].lower()  # Remove ROLE_ prefix and lowercase
                role_emails_str = getattr(self, field_name, "")
                
                if role_emails_str:
                    # Parse comma-separated emails and strip whitespace
                    emails = [email.strip() for email in role_emails_str.split(",") if email.strip()]
                    mapping[role_name] = emails
        
        return mapping


settings = Settings()
