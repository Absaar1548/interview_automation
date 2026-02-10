# WebSocket Protocol – Proctoring & Live Interview (v1)

> **Authority Level**: Architectural Contract  
> Depends on:
> - `docs/architecture/interview_state_machine.md`
> - `docs/architecture/api_contracts.md`

This document defines the **authoritative WebSocket protocol** used for:
- Real-time proctoring (video, audio, behavioral)
- Live interview control signals
- Session heartbeats & fault tolerance

This protocol is **state-scoped** and **backend-authoritative**.

---

## 1. Connection Overview

### Endpoint
```
WS /api/v1/proctoring/ws
```

### Authentication
- Candidate connects using magic-link derived token
- Token validated during handshake
- Interview state must be `READY` or `IN_PROGRESS`

If validation fails → socket closed with error code

---

## 2. Connection Lifecycle

### 2.1 Handshake

**Client → Server**
```json
{
  "type": "HANDSHAKE",
  "interview_id": "uuid",
  "candidate_token": "string",
  "client_info": {
    "browser": "Chrome",
    "os": "Windows"
  }
}
```

**Server → Client**
```json
{
  "type": "HANDSHAKE_ACK",
  "state": "IN_PROGRESS",
  "heartbeat_interval_sec": 10
}
```

---

## 3. Message Envelope (All Events)

All messages MUST follow this envelope:

```json
{
  "type": "EVENT_TYPE",
  "timestamp": "ISO-8601",
  "payload": {}
}
```

Unknown message types are ignored and logged.

---

## 4. Heartbeat & Liveness

### 4.1 Client Heartbeat

**Client → Server**
```json
{
  "type": "HEARTBEAT",
  "timestamp": "ISO-8601"
}
```

### 4.2 Server Heartbeat Ack
```json
{
  "type": "HEARTBEAT_ACK"
}
```

**Rules**:
- Missing 3 consecutive heartbeats → socket closed
- Interview state preserved for reconnect window

---

## 5. Video Proctoring Events

### 5.1 Video Frame Sample
```json
{
  "type": "VIDEO_FRAME",
  "payload": {
    "frame_id": "uuid",
    "image_base64": "string",
    "resolution": "640x480"
  }
}
```

**Notes**:
- Frames sampled every 2–3 seconds
- Backend may drop frames under load

---

## 6. Audio Proctoring Events

### 6.1 Audio Chunk
```json
{
  "type": "AUDIO_CHUNK",
  "payload": {
    "chunk_id": "uuid",
    "audio_base64": "string",
    "duration_ms": 500
  }
}
```

---

## 7. Behavioral & Browser Events

### 7.1 Browser Violation
```json
{
  "type": "BROWSER_EVENT",
  "payload": {
    "event": "TAB_SWITCH | COPY_PASTE | DEVTOOLS_OPEN",
    "confidence": 1.0
  }
}
```

---

## 8. Server-to-Client Control Events

### 8.1 Warning
```json
{
  "type": "WARNING",
  "payload": {
    "message": "Multiple faces detected"
  }
}
```

### 8.2 Termination
```json
{
  "type": "TERMINATE",
  "payload": {
    "reason": "Hard fraud violation"
  }
}
```

Client MUST immediately stop capture on TERMINATE.

---

## 9. Reconnection Rules

- Client may reconnect within **60 seconds**
- Interview state must still be `IN_PROGRESS`
- Reconnect requires fresh HANDSHAKE

---

## 10. State Enforcement

| Interview State | Socket Allowed |
|----------------|---------------|
| READY          | YES           |
| IN_PROGRESS    | YES           |
| COMPLETED      | NO            |
| TERMINATED     | NO            |

---

## 11. Security & Cost Controls

- Frame & audio rate limits enforced
- Payload size limits
- All events logged as metadata (no raw media persistence by default)

---

## 12. Change Policy

This protocol is authoritative.

Any changes require:
- Backend approval
- Frontend capture validation
- Fraud model impact review

