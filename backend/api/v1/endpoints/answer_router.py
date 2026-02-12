from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import uuid
import asyncio

router = APIRouter()

@router.websocket("/ws")
async def answer_websocket(websocket: WebSocket):
    await websocket.accept()
    
    current_question_id = None
    
    try:
        while True:
            # Receive message (can be text or binary)
            message = await websocket.receive()
            
            if message["type"] == "websocket.disconnect":
                break
            
            if "text" in message:
                try:
                    import json
                    data = json.loads(message["text"])
                    msg_type = data.get("type")
                    
                    if msg_type == "START_ANSWER":
                        current_question_id = data.get("question_id")
                        # Ready to receive binary
                        
                    elif msg_type == "END_ANSWER":
                        # Simulate processing delay if needed, but requested immediately
                        
                        # 1. Send Transcript
                        await websocket.send_json({
                            "type": "TRANSCRIPT_FINAL",
                            "text": "This is a mock final transcription."
                        })
                        
                        # 2. Send Answer Ready
                        transcript_id = str(uuid.uuid4())
                        await websocket.send_json({
                            "type": "ANSWER_READY",
                            "transcript_id": transcript_id
                        })
                        
                except json.JSONDecodeError:
                    pass
            
            # Start/End logic handles flow. Binary messages are ignored effectively here 
            # as we only react to specific JSON text messages.
            
    except WebSocketDisconnect:
        pass
