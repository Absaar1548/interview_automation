"""
session_router.py
=================
Endpoints used by the interview shell (InterviewShell, InterviewService, ControlWebSocket).

Routes (all under /api/v1 prefix added in main.py):
  WS  /proctoring/ws                – WebSocket proctoring / control channel
  POST /session/start               – Start a session, returns {state}
  GET  /question/next               – Return next unanswered question
  POST /submit/submit               – Record answer, return next state
  POST /proctoring/event            – Acknowledge a proctoring event

Auth:
  REST  → Authorization: Bearer <jwt>  +  X-Interview-Id: <session_id>
  WS    → HANDSHAKE message {type, interview_id, candidate_token}
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, Header, HTTPException, WebSocket, WebSocketDisconnect, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.v1.auth_router import get_current_active_user
from app.db.database import get_database
from app.db.models.user import UserInDB

logger = logging.getLogger(__name__)

router = APIRouter()


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _get_session_and_interview(
    session_id: str,
    db: AsyncIOMotorDatabase,
) -> tuple[dict, dict]:
    """
    Validate session_id and return (session_doc, interview_doc).
    Raises 404 / 400 on failure.
    """
    try:
        oid = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"Invalid session_id: {session_id}")

    sessions = db.get_collection("interview_sessions")
    session = await sessions.find_one({"_id": oid, "status": "active"})
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Session not found or not active")

    interviews = db.get_collection("interviews")
    interview_oid = ObjectId(session["interview_id"])
    interview = await interviews.find_one({"_id": interview_oid})
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Interview not found")

    return session, interview


async def _get_current_candidate(
    current_user: UserInDB = Depends(get_current_active_user),
) -> UserInDB:
    if current_user.role != "candidate":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only candidates can access this endpoint")
    return current_user


# ─── WebSocket proctoring/control channel ─────────────────────────────────────

@router.websocket("/proctoring/ws")
async def proctoring_ws(websocket: WebSocket, db: AsyncIOMotorDatabase = Depends(get_database)):
    """
    Simple proctoring / control WebSocket.
    Protocol:
      Client → HANDSHAKE {type, interview_id, candidate_token}
      Server → HANDSHAKE_ACK {type, heartbeat_interval_sec}
      Client → HEARTBEAT {type}
      Server → HEARTBEAT_ACK {type}
    """
    await websocket.accept()
    session_validated = False

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "ERROR", "detail": "Invalid JSON"}))
                continue

            msg_type = msg.get("type", "")

            if msg_type == "HANDSHAKE":
                session_id = msg.get("interview_id", "")
                # Validate session exists
                try:
                    oid = ObjectId(session_id)
                    sessions = db.get_collection("interview_sessions")
                    session = await sessions.find_one({"_id": oid, "status": "active"})
                    if session:
                        session_validated = True
                except Exception:
                    session_validated = False

                if session_validated:
                    await websocket.send_text(json.dumps({
                        "type": "HANDSHAKE_ACK",
                        "heartbeat_interval_sec": 30,
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "ERROR",
                        "detail": "Invalid session",
                    }))
                    await websocket.close(code=1008, reason="Invalid session")
                    return

            elif msg_type == "HEARTBEAT":
                await websocket.send_text(json.dumps({"type": "HEARTBEAT_ACK"}))

    except WebSocketDisconnect:
        logger.info("[proctoring_ws] Client disconnected")
    except Exception as exc:
        logger.error("[proctoring_ws] Unexpected error: %s", exc)


@router.websocket("/proctoring/media/ws")
async def proctoring_media_ws(websocket: WebSocket):
    """
    Mock media streaming WebSocket.
    Accepts binary data and discards it.
    """
    await websocket.accept()
    try:
        while True:
            # Just drain the socket
            await websocket.receive_bytes()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass


@router.websocket("/answer/ws")
async def answer_ws(websocket: WebSocket, db: AsyncIOMotorDatabase = Depends(get_database)):
    """
    Mock answer transcription WebSocket.
    Handles START_ANSWER, accepts binary audio, sends mock TRANSCRIPT_* messages,
    and finishes with ANSWER_READY.
    """
    await websocket.accept()
    transcript_id = str(ObjectId())
    
    try:
        while True:
            # Receive text (JSON) or binary
            message = await websocket.receive()
            
            if "text" in message:
                try:
                    data = json.loads(message["text"])
                    msg_type = data.get("type")

                    if msg_type == "START_ANSWER":
                        # Acknowledge or just get ready
                        pass
                        
                    elif msg_type == "END_ANSWER":
                        # Send mock final transcript
                        await websocket.send_text(json.dumps({
                            "type": "TRANSCRIPT_FINAL", 
                            "text": "This is a mock transcript of the candidate's answer."
                        }))
                        
                        # Send answer ready signal
                        await websocket.send_text(json.dumps({
                            "type": "ANSWER_READY", 
                            "transcript_id": transcript_id
                        }))
                        
                        # Close after successful flow
                        await websocket.close()
                        return

                except json.JSONDecodeError:
                    pass

            elif "bytes" in message:
                # Received audio chunk - simulate partial transcript occasionally
                # For now, we can just ignore it or send a partial update
                # await websocket.send_text(json.dumps({"type": "TRANSCRIPT_PARTIAL", "text": "Listening..."}))
                pass

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.error("[answer_ws] Unexpected error: %s", exc)


# ─── REST endpoints ────────────────────────────────────────────────────────────

@router.post("/session/start")
async def session_start(
    x_interview_id: Optional[str] = Header(None, alias="X-Interview-Id"),
    current_user: UserInDB = Depends(_get_current_candidate),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Mark the session as fully active and return {state: "IN_PROGRESS"}.
    The session_id comes via the X-Interview-Id header (set by apiClient).
    """
    if not x_interview_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="X-Interview-Id header is required")

    session, interview = await _get_session_and_interview(x_interview_id, db)

    # Ensure interview belongs to this candidate
    if interview.get("candidate_id") != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Session does not belong to you")

    # Initialise question tracking if not already present
    sessions = db.get_collection("interview_sessions")
    if "answered_count" not in session:
        await sessions.update_one(
            {"_id": session["_id"]},
            {"$set": {"answered_count": 0}},
        )

    return {"state": "IN_PROGRESS"}


@router.get("/question/next")
async def question_next(
    x_interview_id: Optional[str] = Header(None, alias="X-Interview-Id"),
    current_user: UserInDB = Depends(_get_current_candidate),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Return the next unanswered curated question for this session.
    Questions are served in order based on answered_count stored on the session.
    """
    if not x_interview_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="X-Interview-Id header is required")

    session, interview = await _get_session_and_interview(x_interview_id, db)

    if interview.get("candidate_id") != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Session does not belong to you")

    curated = interview.get("curated_questions", {})
    questions: list = curated.get("questions", []) if isinstance(curated, dict) else []
    answered_count: int = session.get("answered_count", 0)

    if answered_count >= len(questions):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="No more questions")

    q = questions[answered_count]
    # Map to the shape QuestionResponse expects on the frontend
    answer_mode = "TEXT"
    if q.get("question_type") == "coding":
        answer_mode = "CODE"
    elif q.get("question_type") == "conversational":
        answer_mode = "AUDIO"

    return {
        "question_id": q.get("question_id", f"q_{answered_count}"),
        "question_text": q.get("prompt", ""),
        "answer_mode": answer_mode,
        "time_limit_sec": q.get("time_limit_sec", 120),
        "question_number": answered_count + 1,
        "total_questions": len(questions),
    }


@router.post("/submit/submit")
async def submit_answer(
    payload: dict,
    x_interview_id: Optional[str] = Header(None, alias="X-Interview-Id"),
    current_user: UserInDB = Depends(_get_current_candidate),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Record the answer and advance the question counter.
    Returns {state: "IN_PROGRESS"} if more questions remain, {state: "COMPLETED"} otherwise.
    """
    if not x_interview_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="X-Interview-Id header is required")

    session, interview = await _get_session_and_interview(x_interview_id, db)

    if interview.get("candidate_id") != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Session does not belong to you")

    curated = interview.get("curated_questions", {})
    questions: list = curated.get("questions", []) if isinstance(curated, dict) else []
    answered_count: int = session.get("answered_count", 0)

    new_count = answered_count + 1

    sessions = db.get_collection("interview_sessions")
    interviews = db.get_collection("interviews")
    now = datetime.utcnow()

    if new_count >= len(questions):
        # All questions answered → complete
        await sessions.update_one(
            {"_id": session["_id"]},
            {"$set": {"answered_count": new_count, "status": "completed", "completed_at": now}},
        )
        await interviews.update_one(
            {"_id": interview["_id"]},
            {"$set": {"status": "completed", "completed_at": now, "updated_at": now}},
        )
        return {"state": "COMPLETED"}
    else:
        await sessions.update_one(
            {"_id": session["_id"]},
            {"$set": {"answered_count": new_count}},
        )
        return {"state": "IN_PROGRESS"}


@router.post("/proctoring/event")
async def proctoring_event(
    payload: dict,
    x_interview_id: Optional[str] = Header(None, alias="X-Interview-Id"),
    current_user: UserInDB = Depends(_get_current_candidate),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Acknowledge a proctoring event. For now just logs and acks."""
    logger.info(
        "[proctoring_event] session=%s user=%s event=%s",
        x_interview_id,
        str(current_user.id),
        payload.get("event_type"),
    )
    return {"acknowledged": True}
