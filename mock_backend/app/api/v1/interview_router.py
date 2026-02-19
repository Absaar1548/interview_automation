"""
Interview Router — Admin-only scheduling endpoints
----------------------------------------------------
POST   /admin/interviews/schedule          – Create a new scheduled interview
PUT    /admin/interviews/{id}/reschedule   – Move interview to a new datetime
PUT    /admin/interviews/{id}/cancel       – Cancel a non-completed interview
"""

from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

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
from app.services.interview_service import InterviewService

router = APIRouter()


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
