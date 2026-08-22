from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FormType(str, Enum):
    RTI_APPLICATION = "rti_application"
    CONSUMER_COMPLAINT = "consumer_complaint"
    MUNICIPAL_GRIEVANCE = "municipal_grievance"
    CYBERCRIME_REPORT = "cybercrime_report"
    TENANCY_DISPUTE = "tenancy_dispute"
    GENERAL_LEGAL_NOTICE = "general_legal_notice"


class FormSessionStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class FormSessionCreate(BaseModel):
    form_type: FormType
    title: Optional[str] = Field(None, max_length=200)
    jurisdiction: Optional[str] = Field(None, max_length=100)
    initial_input: Optional[str] = Field(None, max_length=5000, description="User's initial problem description")


class FormStepSubmit(BaseModel):
    field_updates: Dict[str, Any] = Field(default_factory=dict, description="Key-value field updates")
    user_response: Optional[str] = Field(None, max_length=5000, description="Natural language response to AI question")


class FormStepGuidance(BaseModel):
    step_number: int
    step_title: str
    prompt_question: str
    required_fields: List[str]
    suggested_inputs: List[str] = Field(default_factory=list)
    legal_tips: List[str] = Field(default_factory=list)


class FormSessionResponse(BaseModel):
    id: str
    user_id: str
    form_type: FormType
    title: str
    status: FormSessionStatus
    current_step: int
    total_steps: int
    collected_data: Dict[str, Any] = Field(default_factory=dict)
    missing_fields: List[str] = Field(default_factory=list)
    next_step_guidance: Optional[FormStepGuidance] = None
    created_at: datetime
    updated_at: datetime


class FormCompleteResponse(BaseModel):
    session_id: str
    form_type: FormType
    status: FormSessionStatus
    collected_data: Dict[str, Any]
    ready_for_drafting: bool = True
    complaint_id: Optional[str] = None
