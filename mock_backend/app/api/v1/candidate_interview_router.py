"""
Candidate Interview Router
--------------------------
Endpoints for candidates to view and start their assigned interviews.

GET  /active               – Returns scheduled/in_progress interview for the logged-in candidate
POST /{interview_id}/start – Creates or resumes an interview session
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.api.v1.auth_router import get_current_active_user
from app.db.database import get_database
from app.db.models.user import UserInDB
from app.db.repositories.interview_repository import InterviewRepository

router = APIRouter()


# ─── Candidate auth guard ─────────────────────────────────────────────────────

async def get_current_candidate(
    current_user: UserInDB = Depends(get_current_active_user),
) -> UserInDB:
    if current_user.role != "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only candidates can access this endpoint",
        )
    return current_user


# ─── GET /active ──────────────────────────────────────────────────────────────

@router.get(
    "/active",
    summary="Get the candidate's active or in-progress interview",
    description=(
        "Returns the scheduled or in_progress interview for the logged-in candidate. "
        "For in_progress interviews it also returns the active session_id so the candidate "
        "can rejoin. Returns null when no active interview exists."
    ),
)
async def get_active_interview(
    current_candidate: UserInDB = Depends(get_current_candidate),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    repo = InterviewRepository(db)
    candidate_id = str(current_candidate.id)

    interview = await repo.get_active_or_inprogress_for_candidate(candidate_id)
    if not interview:
        return None

    interview_id = str(interview["_id"])
    interview_status = interview.get("status")

    # ── Scheduled: compute can_start from scheduled_at ─────────────────────
    if interview_status == "scheduled":
        scheduled_at: datetime = interview.get("scheduled_at")
        now_utc = datetime.utcnow()
        # Make comparison offset-naive
        sa_naive = scheduled_at.replace(tzinfo=None) if scheduled_at and scheduled_at.tzinfo else scheduled_at
        can_start = sa_naive is not None and sa_naive <= now_utc
        return {
            "interview_id": interview_id,
            "session_id": None,
            "status": "scheduled",
            "scheduled_at": scheduled_at,
            "can_start": can_start,
        }

    # ── In-progress: return existing session_id for rejoin ─────────────────
    if interview_status == "in_progress":
        sessions = db.get_collection("interview_sessions")
        session = await sessions.find_one(
            {"interview_id": interview_id, "status": "active"}
        )
        session_id = str(session["_id"]) if session else None
        return {
            "interview_id": interview_id,
            "session_id": session_id,
            "status": "in_progress",
            "scheduled_at": interview.get("scheduled_at"),
            "can_start": True,
        }

    return None


# ─── POST /{interview_id}/start ───────────────────────────────────────────────

@router.post(
    "/{interview_id}/start",
    summary="Start or rejoin an interview session",
    description=(
        "Validates the interview belongs to the candidate and is in 'scheduled' "
        "status with scheduled_at <= now. Creates a new session (or returns the "
        "existing one) and transitions the interview to 'in_progress'."
    ),
)
async def start_interview(
    interview_id: str,
    current_candidate: UserInDB = Depends(get_current_candidate),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    # Validate ObjectId
    try:
        ObjectId(interview_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid interview_id: {interview_id}",
        )

    repo = InterviewRepository(db)
    candidate_id = str(current_candidate.id)

    interview = await repo.get_by_id(interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found",
        )

    # Ownership check
    if interview.get("candidate_id") != candidate_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This interview does not belong to you",
        )

    current_status = interview.get("status")

    # If already in_progress → idempotent rejoin
    if current_status == "in_progress":
        sessions = db.get_collection("interview_sessions")
        session = await sessions.find_one(
            {"interview_id": interview_id, "status": "active"}
        )
        session_id = str(session["_id"]) if session else None
        return {
            "session_id": session_id,
            "interview_id": interview_id,
            "status": "in_progress",
        }

    # Must be scheduled to start
    if current_status != "scheduled":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot start interview with status '{current_status}'",
        )

    # Time gate: scheduled_at must be <= now (UTC)
    scheduled_at: datetime = interview.get("scheduled_at")
    if scheduled_at:
        now_utc = datetime.utcnow()
        sa_naive = scheduled_at.replace(tzinfo=None) if scheduled_at.tzinfo else scheduled_at
        if sa_naive > now_utc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Interview cannot be started before the scheduled time",
            )

    # Create / return session
    result = await repo.start_interview(interview_id, candidate_id)
    return {
        "session_id": result["session_id"],
        "interview_id": interview_id,
        "status": "in_progress",
    }
