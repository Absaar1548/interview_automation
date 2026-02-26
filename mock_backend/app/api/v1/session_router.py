"""
session_router.py (Refactored for SQLAlchemy)
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
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth_router import get_current_active_user
from app.db.sql.session import get_db_session, AsyncSessionLocal
from app.db.sql.models.user import User
from app.db.sql.enums import UserRole
from app.services.interview_session_sql_service import InterviewSessionSQLService

logger = logging.getLogger(__name__)

router = APIRouter()


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _get_current_candidate(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role != UserRole.CANDIDATE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only candidates can access this endpoint")
    return current_user

def validate_uuid(id_str: str) -> uuid.UUID:
    try:
        return uuid.UUID(id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID: {id_str}",
        )


# ─── WebSocket proctoring/control channel ─────────────────────────────────────

@router.websocket("/proctoring/ws")
async def proctoring_ws(websocket: WebSocket):
    """
    Simple proctoring / control WebSocket.
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
                session_id_str = msg.get("interview_id", "")
                
                try:
                    session_id = uuid.UUID(session_id_str)
                    
                    # Manual short-lived transaction for WebSocket
                    async with AsyncSessionLocal() as session:
                        await InterviewSessionSQLService.validate_session(session, session_id)
                        
                    session_validated = True
                except (ValueError, HTTPException):
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
    await websocket.accept()
    try:
        while True:
            await websocket.receive_bytes()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass


@router.websocket("/answer/ws")
async def answer_ws(websocket: WebSocket):
    await websocket.accept()
    transcript_id = str(uuid.uuid4())
    
    try:
        while True:
            message = await websocket.receive()
            if "text" in message:
                try:
                    data = json.loads(message["text"])
                    if data.get("type") == "END_ANSWER":
                        await websocket.send_text(json.dumps({
                            "type": "TRANSCRIPT_FINAL", 
                            "text": "This is a mock transcript of the candidate's answer."
                        }))
                        await websocket.send_text(json.dumps({
                            "type": "ANSWER_READY", 
                            "transcript_id": transcript_id
                        }))
                        await websocket.close()
                        return
                except json.JSONDecodeError:
                    pass
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.error("[answer_ws] Unexpected error: %s", exc)


# ─── REST endpoints ────────────────────────────────────────────────────────────

@router.post("/session/start")
async def session_start(
    x_interview_id: Optional[str] = Header(None, alias="X-Interview-Id"),
    current_user: User = Depends(_get_current_candidate),
    session: AsyncSession = Depends(get_db_session),
):
    if not x_interview_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Interview-Id header is required")

    session_id = validate_uuid(x_interview_id)
    candidate_id = current_user.id
    
    # Ensures the session exists and belongs to the candidate
    await InterviewSessionSQLService.validate_session(session, session_id, candidate_id)

    return {"state": "IN_PROGRESS"}


@router.get("/question/next")
async def question_next(
    x_interview_id: Optional[str] = Header(None, alias="X-Interview-Id"),
    current_user: User = Depends(_get_current_candidate),
    session: AsyncSession = Depends(get_db_session),
):
    if not x_interview_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Interview-Id header is required")

    session_id = validate_uuid(x_interview_id)
    candidate_id = current_user.id

    return await InterviewSessionSQLService.get_session_state(session, session_id, candidate_id)


@router.post("/submit/submit")
async def submit_answer(
    payload: dict,
    x_interview_id: Optional[str] = Header(None, alias="X-Interview-Id"),
    current_user: User = Depends(_get_current_candidate),
    session: AsyncSession = Depends(get_db_session),
):
    if not x_interview_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Interview-Id header is required")

    session_id = validate_uuid(x_interview_id)
    candidate_id = current_user.id

    return await InterviewSessionSQLService.submit_answer(session, session_id, candidate_id, payload)


@router.post("/proctoring/event")
async def proctoring_event(
    payload: dict,
    x_interview_id: Optional[str] = Header(None, alias="X-Interview-Id"),
    current_user: User = Depends(_get_current_candidate),
    session: AsyncSession = Depends(get_db_session),
):
    if not x_interview_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Interview-Id header is required")
        
    session_id = validate_uuid(x_interview_id)
    await InterviewSessionSQLService.validate_session(session, session_id, current_user.id)
    
    logger.info(
        "[proctoring_event] session=%s user=%s event=%s",
        session_id,
        str(current_user.id),
        payload.get("event_type"),
    )
    return {"acknowledged": True}
