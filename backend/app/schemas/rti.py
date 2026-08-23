"""
Pydantic schemas for RTI Drafting Agent request and response payloads.
"""
from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.rag import Citation


class RTIDraftRequest(BaseModel):
    """
    Request model for generating a structured RTI Application draft.
    """
    request: str = Field(
        ...,
        min_length=3,
        description="Plain-language description of information requested by citizen",
    )
    applicant_name: Optional[str] = Field(
        default=None,
        description="Optional name of applicant (if missing, bracketed placeholder is used)",
    )
    applicant_address: Optional[str] = Field(
        default=None,
        description="Optional postal address of applicant (if missing, bracketed placeholder is used)",
    )
    public_authority: Optional[str] = Field(
        default=None,
        description="Optional target public authority / department name",
    )


class RTIDraftResponse(BaseModel):
    """
    Response model containing the generated RTI application draft and verified citations.
    """
    draft: str = Field(..., description="Formatted RTI Application draft string")
    limitations: Optional[str] = Field(
        default=None,
        description="Explicit note on missing details or placeholders used",
    )
    citations: List[Citation] = Field(
        default_factory=list,
        description="Verified statutory legal citations from RTI Act, 2005",
    )
