"""
Pydantic schemas for Stage 5A Grounded Answer Generation.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class GenerationResponse(BaseModel):
    """
    Structured response returned by the Grounded Answer Generator.
    """
    answer: str = Field(..., description="Grounded, plain-language answer derived strictly from retrieved legal sources.")
    limitations: Optional[str] = Field(default=None, description="Explicit statement of any info absent from retrieved context.")
    source_ids: List[str] = Field(default_factory=list, description="List of chunk IDs actually used to ground the answer.")
