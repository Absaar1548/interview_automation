# Phase 1 Mock Backend Specification

## 1. Overview
The **Phase 1 Mock Backend** is a self-contained, in-memory implementation designed to facilitate frontend development without external dependencies.

- **Deterministic Behavior**: All responses, including questions and evaluation results, are fixed and predictable.
- **In-Memory Storage**: State is maintained in a global dictionary and resets on server restart.
- **Backend-Authoritative State Machine**: Strict enforcement of interview progression.
- **No Database**: Data persistence is not implemented.
- **No AI**: Scoring and feedback are simulated.
- **No External Integrations**: Zwayam and other services are mocked.

---

## 2. Interview State Machine

### States
- `CREATED`: Initial state after token validation.
- `RESUME_PARSED`: Resume analysis complete (auto-transition).
- `READY`: System ready for candidate (auto-transition).
- `IN_PROGRESS`: Interview started.
- `QUESTION_ASKED`: Question delivered to candidate.
- `ANSWER_SUBMITTED`: Candidate response received.
- `EVALUATING`: Answer processing (simulated).
- `COMPLETED`: All questions answered.
- `TERMINATED`: Hard violation detected or manual stop.

### Transitions
```text
CREATED → RESUME_PARSED
RESUME_PARSED → READY
READY → IN_PROGRESS
IN_PROGRESS → QUESTION_ASKED
QUESTION_ASKED → ANSWER_SUBMITTED
ANSWER_SUBMITTED → EVALUATING
EVALUATING → IN_PROGRESS (if more questions) | COMPLETED (if finished)
ANY_STATE → TERMINATED (on hard violation)
```

- **Single Active Interview**: A candidate token can only have one active interview at a time.
- **Violations**: Hard violations transition immediately to `TERMINATED`. Soft violations increase cheat score but maintain state.

---

## 3. Global API Conventions

**Base Path**: `/api/v1`

**Headers**:
- `X-Interview-Id` (Required for all endpoints except `/session/init` and `/dev/bootstrap`)

**CORS**:
- Allowed Origin: `http://localhost:3000`

**Error Format**:
```json
{
  "error_code": "INVALID_STATE",
  "message": "Cannot perform action in current state",
  "current_state": "COMPLETED"
}
```

---

## 4. REST Endpoints

### 4.1 Developer Tools

**GET /dev/bootstrap**
- **Purpose**: Development helper to create a valid session ready for testing.
- **Behavior**:
    1. Removes any existing session for `dev-candidate-token`.
    2. Creates a new session.
    3. Fast-forwards state to `READY`.
- **Response**:
```json
{
  "interview_id": "uuid",
  "candidate_token": "dev-candidate-token"
}
```

### 4.2 Session Management

**POST /session/init**
- **State**: `CREATED` (transition → `RESUME_PARSED`)
- **Request**: `{ "candidate_token": "string" }`
- **Response**:
```json
{
  "interview_id": "uuid",
  "state": "RESUME_PARSED"
}
```

**POST /session/start**
- **State**: `READY` (transition → `IN_PROGRESS`)
- **Header**: `X-Interview-Id`
- **Behavior**:
    - Validates state is `READY` or already `IN_PROGRESS`.
    - Updates state to `IN_PROGRESS`.
- **Response**:
```json
{
  "state": "IN_PROGRESS",
  "first_question_ready": true
}
```

### 4.3 Interview Flow

**GET /questions/next**
- **State**: `IN_PROGRESS` (transition → `QUESTION_ASKED`)
- **Header**: `X-Interview-Id`
- **Response**:
```json
{
  "question_id": "q1",
  "category": "CONVERSATIONAL",
  "answer_mode": "AUDIO",
  "difficulty": "EASY",
  "prompt": "Tell me about yourself...",
  "time_limit_sec": 30
}
```

**POST /evaluation/submit**
- **State**: `QUESTION_ASKED` (transition → `ANSWER_SUBMITTED` → `EVALUATING` → `IN_PROGRESS`|`COMPLETED`)
- **Header**: `X-Interview-Id`
- **Request**:
```json
{
  "question_id": "uuid",
  "answer_type": "AUDIO",
  "answer_payload": "base64/text"
}
```
- **Response**:
```json
{
  "state": "IN_PROGRESS"
}
```
*Note: If `question_id` is "q4", state becomes `COMPLETED`.*

**GET /summary**
- **State**: `COMPLETED` | `TERMINATED`
- **Header**: `X-Interview-Id`
- **Response**:
```json
{
  "final_score": 80,
  "recommendation": "PROCEED",
  "fraud_risk": "LOW",
  "strengths": ["Good communication", "Strong Python basics"],
  "gaps": ["Algorithm optimization"],
  "notes": "Mock evaluation summary"
}
```

### 4.4 Utilities

**GET /code/template/{question_id}**
- **State**: `IN_PROGRESS`
- **Header**: `X-Interview-Id`
- **Response**:
```json
{
  "language": "python",
  "starter_code": "# Write your solution here\n"
}
```

**GET /conversation/prompt**
- **State**: `IN_PROGRESS`
- **Header**: `X-Interview-Id`
- **Response**:
```json
{
  "prompt": "Can you elaborate more on your previous experience?",
  "followup_allowed": true
}
```

### 4.5 Integrations

**POST /proctoring/event**
- **State**: `IN_PROGRESS`
- **Header**: `X-Interview-Id`
- **Request**:
```json
{
  "event_type": "TAB_SWITCH",
  "confidence": 0.95
}
```
- **Response**: `{ "action": "FLAG" }` or `{ "action": "TERMINATE" }` or `{ "action": "IGNORE" }`

**POST /zwayam/push-feedback**
- **State**: `COMPLETED` | `TERMINATED`
- **Header**: `X-Interview-Id`
- **Request**:
```json
{
  "decision": "PROCEED",
  "final_score": 85,
  "fraud_summary": "None"
}
```
- **Response**: `{ "status": "SYNCED" }`

---

## 5. WebSocket Protocol

### 5.1 Proctoring Signaling (`/api/v1/proctoring/ws`)

**1. Connection & Handshake**
- **Client**: Connects to WS.
- **Client Sends**:
```json
{
  "type": "HANDSHAKE",
  "interview_id": "uuid",
  "candidate_token": "string"
}
```
- **Server Validates**: State matches `READY` or `IN_PROGRESS`.
- **Server Responds**:
```json
{
  "type": "HANDSHAKE_ACK",
  "state": "IN_PROGRESS",
  "heartbeat_interval_sec": 10
}
```
*Note: Invalid handshake closes connection with code 1008.*

**2. Heartbeat**
- **Client Sends**: `{ "type": "HEARTBEAT" }`
- **Server Responds**: `{ "type": "HEARTBEAT_ACK" }`

**3. Termination**
- If server detects `TERMINATED` state (due to hard violation via REST), it pushes:
```json
{
  "type": "TERMINATE",
  "payload": {
    "reason": "Hard fraud violation"
  }
}
```
- Server closes connection.

### 5.2 Proctoring Media (`/api/v1/proctoring/media/ws`)
- **Behavior**: Dummy sink. Accepts all binary/text messages and ignores them.
- **Connection**: Kept open indefinitely until client disconnects.

### 5.3 Answer Streaming (`/api/v1/answer/ws`)

**Protocol**:
1. **Client Sends Text**: `{ "type": "START_ANSWER", "question_id": "..." }`
2. **Client Sends Binary**: Audio chunks (ignored by mock).
3. **Client Sends Text**: `{ "type": "END_ANSWER" }`
4. **Server Responds**:
   - `{ "type": "TRANSCRIPT_FINAL", "text": "This is a mock final transcription." }`
   - `{ "type": "ANSWER_READY", "transcript_id": "uuid" }`

---

## 6. Deterministic Question Set

The backend serves exactly 4 questions in this order:

| ID | Category | Type | Difficulty | Prompt | Time (s) |
|----|----------|------|------------|--------|----------|
| q1 | CONVERSATIONAL | AUDIO | EASY | Tell me about yourself... | 30 |
| q2 | STATIC | AUDIO | MEDIUM | What is the difference between... | 45 |
| q3 | CODING | CODE | MEDIUM | Write a function to reverse... | 300 |
| q4 | CODING | CODE | HARD | Implement binary search... | 300 |

---

## 7. Proctoring Rules

### Hard Violations (Action: TERMINATE)
- `MULTI_FACE`: Multiple people detected.
- `VOICE_MISMATCH`: Voice print does not match.

### Soft Violations (Action: FLAG)
- `TAB_SWITCH`: Focus lost. Adds +10 to cheat score.

---

## 8. Known Phase 1 Limitations
- **No Persistence**: Restarting the backend wipes all data.
- **No Reconnect Window**: Disconnecting WS does not start a grace period timer.
- **No Heartbeat Timeout**: Server does not close connection if client stops sending heartbeats.
- **No AI Scoring**: Scores are hardcoded/simulated.
- **No Fraud ML**: Fraud detection logic is trusted from client input.
