from fastapi import APIRouter, HTTPException, Header, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
import asyncio
import json

# Import mock backend components
from mock_backend.interview_store import (
    get_interview,
    add_cheat_score,
    terminate_interview
)
from mock_backend.state_machine import InterviewState

router = APIRouter()

class ProctoringEventRequest(BaseModel):
    event_type: str = Field(..., pattern="^(TAB_SWITCH|MULTI_FACE|VOICE_MISMATCH)$")
    confidence: float

class ProctoringEventResponse(BaseModel):
    action: str

# --- REST ENDPOINT ---

@router.post("/event", response_model=ProctoringEventResponse)
def proctoring_event(
    request: ProctoringEventRequest,
    x_interview_id: str = Header(..., alias="X-Interview-Id")
):
    session = get_interview(x_interview_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
        
    if session.state != InterviewState.IN_PROGRESS:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_STATE",
                "message": f"Cannot process proctoring event in state {session.state.value}",
                "current_state": session.state.value
            }
        )
    
    # Hard violations
    if request.event_type in ["MULTI_FACE", "VOICE_MISMATCH"]:
        terminate_interview(session)
        return {"action": "TERMINATE"}
    
    # Soft violations
    elif request.event_type == "TAB_SWITCH":
        add_cheat_score(session, 10)
        return {"action": "FLAG"}
    
    # Default behavior
    return {"action": "IGNORE"}


# --- WEBSOCKET ENDPOINT (SIGNALING) ---

@router.websocket("/ws")
async def proctoring_websocket(websocket: WebSocket):
    await websocket.accept()
    
    session = None
    
    try:
        # 1. Wait for HANDSHAKE
        data = await websocket.receive_json()
        
        if data.get("type") != "HANDSHAKE":
            await websocket.close(code=1008, reason="Expected HANDSHAKE")
            return
            
        interview_id = data.get("interview_id")
        candidate_token = data.get("candidate_token")
        
        session = get_interview(interview_id)
        
        # Validate session
        if not session or session.candidate_token != candidate_token:
            await websocket.close(code=1008, reason="Invalid session or token")
            return
            
        # Validate state
        if session.state not in [InterviewState.READY, InterviewState.IN_PROGRESS]:
            await websocket.close(code=1008, reason=f"Invalid state: {session.state.value}")
            return
            
        # Send HANDSHAKE_ACK
        await websocket.send_json({
            "type": "HANDSHAKE_ACK",
            "state": session.state.value,
            "heartbeat_interval_sec": 10
        })
        
        # 2. Main Loop
        while True:
            # Check state before processing (for termination injection)
            if session.state == InterviewState.TERMINATED:
                await websocket.send_json({
                    "type": "TERMINATE",
                    "payload": {
                        "reason": "Hard fraud violation"
                    }
                })
                # We send terminate then close
                await websocket.close()
                break
            
            # Receive message
            # We use a short timeout or just wait. 
            # Since mock backend is synchronous and state changes happen via REST, 
            # we rely on the client sending heartbeats to trigger state checks in this loop,
            # OR we could accept the message and then check state.
            
            data = await websocket.receive_json()
            event_type = data.get("type")
            
            if event_type == "HEARTBEAT":
                # Check state again on heartbeat
                if session.state == InterviewState.TERMINATED:
                    await websocket.send_json({
                        "type": "TERMINATE",
                        "payload": {
                            "reason": "Hard fraud violation"
                        }
                    })
                    await websocket.close()
                    break
                
                await websocket.send_json({
                    "type": "HEARTBEAT_ACK"
                })
            
            # Ignore unknown event types
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        # Close on error
        try:
            await websocket.close(code=1011) # Internal Error
        except:
            pass

# --- WEBSOCKET ENDPOINT (MEDIA DUMMY) ---

@router.websocket("/media/ws")
async def proctoring_media_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Receive and ignore all messages (binary/text)
            await websocket.receive()
    except WebSocketDisconnect:
        pass
