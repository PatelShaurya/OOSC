from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CurrentUser(BaseModel):
    id: str
    email: Optional[str] = None
    role: str = "authenticated"
    is_anonymous: bool = False


class UserProfileResponse(BaseModel):
    id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    preferred_language: str = "en"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=120)
    phone_number: Optional[str] = Field(None, max_length=20)
    state: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    preferred_language: Optional[str] = Field("en", max_length=10)
