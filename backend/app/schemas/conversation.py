from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.rag import Citation


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class FeedbackType(str, Enum):
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    NONE = "none"


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000, description="Message content")
    category: Optional[str] = Field(None, description="Optional legal or civic category")
    jurisdiction: Optional[str] = Field(None, description="State or municipal jurisdiction")
    language: Optional[str] = Field("en", description="Preferred response language")


class MessageFeedbackRequest(BaseModel):
    feedback: FeedbackType
    feedback_notes: Optional[str] = Field(None, max_length=1000)


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: MessageRole
    content: str
    citations: List[Citation] = Field(default_factory=list)
    suggested_followups: List[str] = Field(default_factory=list)
    feedback: FeedbackType = FeedbackType.NONE
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ConversationCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=200, description="Optional conversation title")
    category: Optional[str] = Field(None, description="Civic/legal topic category")
    jurisdiction: Optional[str] = Field(None, description="State/district jurisdiction")
    initial_message: Optional[str] = Field(None, max_length=5000, description="Optional starting message")


class ConversationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = Field(None, max_length=100)
    jurisdiction: Optional[str] = Field(None, max_length=100)


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    category: Optional[str] = None
    jurisdiction: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse] = Field(default_factory=list)
