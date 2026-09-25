from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union

class EnrolledCourseSchema(BaseModel):
    course_id: str = Field(..., description="Unique course identifier or slug")
    course_name: str = Field(..., description="Display title of the course")

class UserProfileResponse(BaseModel):
    id: str = Field(..., description="Supabase Auth UUID")
    email: str = Field(..., description="Primary user email address")
    full_name: Optional[str] = Field(None, description="Full display name")
    avatar_url: Optional[str] = Field(None, description="Profile avatar URL")
    email_verified: Optional[bool] = Field(False, description="Whether email has been verified")
    phone: Optional[str] = Field("", description="Phone number if provided")
    provider: Optional[str] = Field(None, description="OAuth provider (e.g. google)")
    roles: List[str] = Field(default_factory=lambda: ["user"], description="Assigned roles (e.g. ['user'], ['admin'])")
    college: Optional[str] = Field("", description="College / University name")
    graduation_year: Optional[str] = Field("", description="Graduation year (e.g. '2025')")
    branch: Optional[str] = Field("", description="Degree or engineering branch (e.g. 'Computer Science')")
    codeforces_handle: Optional[str] = Field("", description="Linked Codeforces handle for stats")
    social_links: Dict[str, str] = Field(default_factory=dict, description="Dictionary of social links (github, linkedin, twitter)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extensible preferences and arbitrary metadata")
    is_pro_active: bool = Field(False, description="Flag indicating if the user has an active Pro subscription")
    pro_courses: List[EnrolledCourseSchema] = Field(default_factory=list, description="Courses accessible via active Pro subscription")
    purchased_courses: List[EnrolledCourseSchema] = Field(default_factory=list, description="Individually purchased courses")
    enrolled_courses: List[EnrolledCourseSchema] = Field(default_factory=list, description="Unified de-duplicated list of all accessible courses")
    pro_subscription: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Detailed Pro subscription record (expiry, purchases)")
    created_at: Optional[str] = Field(None, description="Account creation timestamp (ISO 8601)")
    last_sign_in_at: Optional[str] = Field(None, description="Last login timestamp (ISO 8601)")
    updated_at: Optional[str] = Field(None, description="Last update timestamp (ISO 8601)")

class ProfileUpdateSchema(BaseModel):
    full_name: Optional[str] = Field(None, description="Full display name")
    college: Optional[str] = Field(None, description="College / University name")
    graduation_year: Optional[str] = Field(None, description="Graduation year (e.g. '2025')")
    branch: Optional[str] = Field(None, description="Degree or branch (e.g. 'CSE')")
    codeforces_handle: Optional[str] = Field(None, description="Codeforces handle")
    social_links: Optional[Dict[str, str]] = Field(None, description="Dictionary of social handles (github, linkedin, twitter)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Arbitrary user preferences/metadata")

class SubscriptionDetailsResponse(BaseModel):
    pro_subscription: Dict[str, Any] = Field(default_factory=dict, description="Pro subscription status, active expiry epoch, history")
    purchased_courses: Dict[str, Any] = Field(default_factory=dict, description="Individually purchased courses array")

class RefreshTokenSchema(BaseModel):
    refresh_token: str = Field(..., description="Supabase refresh token string")

class RefreshTokenResponse(BaseModel):
    access_token: str = Field(..., description="New JWT access token")
    refresh_token: str = Field(..., description="Rotated refresh token")
    expires_in: int = Field(..., description="Token lifespan in seconds")

class TokenStatusResponse(BaseModel):
    authenticated: bool = Field(..., description="Whether the provided token is valid and authenticated")

class LogoutResponse(BaseModel):
    success: bool = Field(True, description="Whether logout was successful")
    message: str = Field("Logged out successfully", description="Status message")
