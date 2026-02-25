"""
Interview Router — Admin-only scheduling endpoints
----------------------------------------------------
POST   /admin/interviews/schedule          – Create a new scheduled interview
PUT    /admin/interviews/{id}/reschedule   – Move interview to a new datetime
PUT    /admin/interviews/{id}/cancel       – Cancel a non-completed interview
"""

from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from bson import ObjectId as BSONObjectId

from app.api.v1.auth_router import get_current_admin
from app.db.database import get_database
from app.db.models.user import UserInDB
from app.schemas.interview import (
    ScheduleInterviewRequest,
    ScheduleInterviewResponse,
    RescheduleInterviewRequest,
    RescheduleInterviewResponse,
    CancelInterviewRequest,
    CancelInterviewResponse,
)
from app.db.repositories.interview_repository import InterviewRepository
from app.services.interview_service import InterviewService

router = APIRouter()


def _serialize_doc(doc: dict) -> dict:
    """Recursively convert all ObjectId values in a MongoDB doc to strings."""
    result = {}
    for key, value in doc.items():
        if isinstance(value, BSONObjectId):
            result[key] = str(value)
        elif isinstance(value, dict):
            result[key] = _serialize_doc(value)
        elif isinstance(value, list):
            result[key] = [
                _serialize_doc(v) if isinstance(v, dict) else (str(v) if isinstance(v, BSONObjectId) else v)
                for v in value
            ]
        else:
            result[key] = value
    return result


@router.get(
    "/templates",
    summary="List active interview templates",
    description="Admin-only. Returns all interview templates with is_active=True.",
)
async def list_templates(
    current_admin: UserInDB = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    cursor = db["interview_templates"].find({"is_active": True})
    templates = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        templates.append(_serialize_doc(doc))
    return templates


@router.get(
    "/summary",
    summary="Get a lightweight summary of all interviews",
    description=(
        "Admin-only. Returns candidate_id, interview_id, status, and scheduled_at "
        "for every interview. Excludes curated_questions for performance."
    ),
)
async def get_interview_summary(
    current_admin: UserInDB = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    repo = InterviewRepository(db)
    return await repo.get_all_summary()


@router.post(
    "/schedule",
    response_model=ScheduleInterviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule a new interview for a candidate",
    description=(
        "Admin-only. Validates candidate eligibility, checks for existing "
        "active interviews, verifies template, and creates the interview document "
        "with a mock curated questions payload."
    ),
)
async def schedule_interview(
    request: ScheduleInterviewRequest,
    current_admin: UserInDB = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    service = InterviewService(db)
    interview = await service.schedule_interview(
        candidate_id=request.candidate_id,
        template_id=request.template_id,
        scheduled_at=request.scheduled_at,
        admin_id=str(current_admin.id),
    )
    return interview


@router.put(
    "/{interview_id}/reschedule",
    response_model=RescheduleInterviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Reschedule an existing interview",
    description=(
        "Admin-only. Moves a 'scheduled' interview to a new future datetime. "
        "Returns 409 if status is anything other than 'scheduled'."
    ),
)
async def reschedule_interview(
    interview_id: str,
    request: RescheduleInterviewRequest,
    current_admin: UserInDB = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    service = InterviewService(db)
    result = await service.reschedule_interview(
        interview_id=interview_id,
        scheduled_at=request.scheduled_at,
    )
    return result


@router.put(
    "/{interview_id}/cancel",
    response_model=CancelInterviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel an interview",
    description=(
        "Admin-only. Cancels an interview by setting status to 'cancelled'. "
        "The document is never deleted. Returns 409 if status is 'completed'."
    ),
)
async def cancel_interview(
    interview_id: str,
    request: CancelInterviewRequest = CancelInterviewRequest(),
    current_admin: UserInDB = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    service = InterviewService(db)
    result = await service.cancel_interview(
        interview_id=interview_id,
        reason=request.reason,
    )
    return result
