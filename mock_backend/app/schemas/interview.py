import uuid
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Any, Literal
from datetime import datetime


# ─── Request Schemas ─────────────────────────────────────────────────────────

class InterviewSessionQuestionCreate(BaseModel):
    """Schema for creating a session question with optional overrides."""
    question_id: Optional[uuid.UUID] = None
    custom_text: Optional[str] = None
    order: int

class ScheduleInterviewRequest(BaseModel):
    """Request body for POST /admin/interviews/schedule"""
    candidate_id: str = Field(..., description="UUID of the candidate user")
    template_id: str = Field(..., description="UUID of the interview template")
    scheduled_at: datetime = Field(..., description="Future UTC datetime for the interview")
    questions: Optional[List[InterviewSessionQuestionCreate]] = Field(None, description="Optional custom questions to override template defaults")
    draft_interview_id: Optional[str] = Field(None, description="UUID of the draft interview to finalize")


class RescheduleInterviewRequest(BaseModel):
    """Request body for PUT /admin/interviews/{id}/reschedule"""
    scheduled_at: datetime = Field(..., description="New future UTC datetime for the interview")


class CancelInterviewRequest(BaseModel):
    """Request body for PUT /admin/interviews/{id}/cancel"""
    reason: Optional[str] = Field(None, description="Optional cancellation reason for audit")


# ─── Response Schemas ─────────────────────────────────────────────────────────

class CuratedQuestionItem(BaseModel):
    """
    A single question in the curated payload.

    Common fields are required for all types.
    Type-specific config blocks are Optional — only the relevant one
    will be populated depending on question_type:
      - "static"         → evaluation_mode + source
      - "conversational" → conversation_config
      - "coding"         → coding_config
    """
    question_id: str
    question_type: Literal["static", "conversational", "coding"]
    order: int
    prompt: str
    text: Optional[str] = None
    difficulty: Literal["easy", "medium", "hard"]
    time_limit_sec: int

    # static-only fields
    evaluation_mode: Optional[str] = None   # e.g. "text"
    source: Optional[str] = None            # e.g. "question_bank"

    # conversational-only fields
    conversation_config: Optional[dict] = None
    # Expected shape:
    # { "follow_up_depth": int, "ai_model": str, "evaluation_mode": str }

    # coding-only fields
    coding_config: Optional[dict] = None
    # Expected shape:
    # { "language": str, "starter_code": str,
    #   "test_cases": [{"input": str, "expected_output": str}],
    #   "execution_timeout_sec": int }

    class Config:
        extra = "allow"   # forward-compatible: extra keys from AI agent won't break deserialization


class TechnicalSection(BaseModel):
    questions: List[CuratedQuestionItem]

class CodingProblemItem(BaseModel):
    problem_id: str
    title: str
    difficulty: str
    description: Optional[str] = None
    starter_code: Optional[dict] = None

class CodingSection(BaseModel):
    problem_solving_type: Optional[Literal["coding", "analytical"]] = "coding"
    problems: Optional[List[CodingProblemItem]] = None
    questions: Optional[List[CuratedQuestionItem]] = None

class ConversationalSection(BaseModel):
    rounds: int

class CuratedQuestionsPayload(BaseModel):
    template_id: str
    generated_from: dict
    generated_at: datetime
    generation_method: str
    questions: Optional[List[CuratedQuestionItem]] = None
    technical_section: Optional[TechnicalSection] = None
    coding_section: Optional[CodingSection] = None
    problem_solving_section: Optional[CodingSection] = None
    conversational_section: Optional[ConversationalSection] = None


class InterviewTemplateResponse(BaseModel):
    id: uuid.UUID
    title: str
    role_name: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    is_default_for_role: bool
    settings: Optional[dict] = None
    technical_config: Optional[dict] = None
    coding_config: Optional[dict] = None
    conversational_config: Optional[dict] = None
    max_duration_minutes: int
    max_technical_questions: int
    max_conversational_questions: int
    max_analytical_questions: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InterviewTemplateCreate(BaseModel):
    title: str
    role_name: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    is_default_for_role: bool = False
    settings: Optional[dict] = None
    technical_config: Optional[dict] = None
    coding_config: Optional[dict] = None
    conversational_config: Optional[dict] = None
    max_duration_minutes: int = Field(default=60, ge=1, le=60, description="Max duration must be 1-60 minutes")
    max_technical_questions: int = Field(default=10, ge=0, le=10, description="Max technical questions must be <= 10")
    max_conversational_questions: int = Field(default=10, ge=0, le=10, description="Max conversational questions must be <= 10")
    max_analytical_questions: int = Field(default=10, ge=0, le=10, description="Max analytical questions must be <= 10")

    @model_validator(mode="after")
    def check_config_question_counts(self) -> "InterviewTemplateCreate":
        # technical_config stores flat counts: {easy, medium, hard}
        if self.technical_config:
            total = (
                (self.technical_config.get("easy") or 0)
                + (self.technical_config.get("medium") or 0)
                + (self.technical_config.get("hard") or 0)
            )
            if total > self.max_technical_questions:
                raise ValueError(
                    f"Total technical questions ({total}) exceed the template limit of {self.max_technical_questions}."
                )

        # conversational_config stores {rounds: int}
        if self.conversational_config:
            rounds = self.conversational_config.get("rounds") or 0
            if rounds > self.max_conversational_questions:
                raise ValueError(
                    f"Conversational rounds ({rounds}) exceed the template limit of {self.max_conversational_questions}."
                )

        # coding_config stores {count: int}
        if self.coding_config:
            count = self.coding_config.get("count") or 0
            limit = self.max_analytical_questions  # same cap for both coding/analytical
            if count > limit:
                raise ValueError(
                    f"Problem solving count ({count}) exceeds the template limit of {limit}."
                )

        return self


class InterviewTemplateUpdate(BaseModel):
    title: Optional[str] = None
    role_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_default_for_role: Optional[bool] = None
    settings: Optional[dict] = None
    technical_config: Optional[dict] = None
    coding_config: Optional[dict] = None
    conversational_config: Optional[dict] = None
    max_duration_minutes: Optional[int] = Field(None, ge=1, le=60, description="Max duration must be 1-60 minutes")
    max_technical_questions: Optional[int] = Field(None, ge=0, le=10, description="Max technical questions must be <= 10")
    max_conversational_questions: Optional[int] = Field(None, ge=0, le=10, description="Max conversational questions must be <= 10")
    max_analytical_questions: Optional[int] = Field(None, ge=0, le=10, description="Max analytical questions must be <= 10")

    @model_validator(mode="after")
    def check_config_question_counts(self) -> "InterviewTemplateUpdate":
        max_tech = self.max_technical_questions if self.max_technical_questions is not None else 10
        max_conv = self.max_conversational_questions if self.max_conversational_questions is not None else 10
        max_prob = self.max_analytical_questions if self.max_analytical_questions is not None else 10

        if self.technical_config:
            total = (
                (self.technical_config.get("easy") or 0)
                + (self.technical_config.get("medium") or 0)
                + (self.technical_config.get("hard") or 0)
            )
            if total > max_tech:
                raise ValueError(
                    f"Total technical questions ({total}) exceed the template limit of {max_tech}."
                )

        if self.conversational_config:
            rounds = self.conversational_config.get("rounds") or 0
            if rounds > max_conv:
                raise ValueError(
                    f"Conversational rounds ({rounds}) exceed the template limit of {max_conv}."
                )

        if self.coding_config:
            count = self.coding_config.get("count") or 0
            if count > max_prob:
                raise ValueError(
                    f"Problem solving count ({count}) exceeds the template limit of {max_prob}."
                )

        return self


class ScheduleInterviewResponse(BaseModel):
    """Response body for POST /admin/interviews/schedule"""
    id: str
    candidate_id: str
    template_id: str
    assigned_by: str
    status: str
    scheduled_at: datetime
    curated_questions: CuratedQuestionsPayload
    created_at: datetime

    class Config:
        from_attributes = True


class CancelInterviewResponse(BaseModel):
    """Response body for PUT /admin/interviews/{id}/cancel"""
    id: str
    status: str
    cancelled_at: datetime
    reason: Optional[str] = None

    class Config:
        from_attributes = True

class RescheduleInterviewResponse(BaseModel):
    """Response body for PUT /admin/interviews/{id}/reschedule"""
    id: str
    status: str
    scheduled_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
