# REST API Contracts – Interview Agent (v1)

> **Authority Level**: Architectural Contract  
> Depends on: `docs/architecture/interview_state_machine.md`

This document defines the **authoritative REST API contracts** between:
- Frontend (Next.js)
- Backend (FastAPI)
- Zwayam Integration Gateway

No implementation details live here. This is a **contract-first specification**.

---

## 1. Global API Conventions

### Base Path
```
/api/v1
```

### Authentication
- Candidate access via **magic link token** (header or query param)
- Admin / internal access via service credentials (out of scope for v1 implementation)

### Common Headers
```
X-Interview-Id: <uuid>
X-Candidate-Token: <opaque-token>
```

### Error Model (Standard)
```json
{
  "error_code": "INVALID_STATE",
  "message": "Action not allowed in current interview state",
  "current_state": "IN_PROGRESS"
}
```

---

## 2. Session & Interview Lifecycle APIs

### 2.1 Initialize Interview Session
**Endpoint**
```
POST /session/init
```

**Allowed State**: `CREATED`

**Request**
```json
{
  "candidate_token": "string"
}
```

**Response**
```json
{
  "interview_id": "uuid",
  "state": "READY"
}
```

---

### 2.2 Start Interview
```
POST /session/start
```

**Allowed State**: `READY`

**Response**
```json
{
  "state": "IN_PROGRESS",
  "first_question_ready": true
}
```

---

## 3. Question Delivery APIs

### 3.1 Fetch Next Question
```
GET /questions/next
```

**Allowed State**: `IN_PROGRESS`

**Response**
```json
{
  "question_id": "uuid",
  "type": "VIDEO | TEXT | CODING",
  "difficulty": "EASY | MEDIUM | HARD",
  "prompt": "string",
  "time_limit_sec": 300
}
```

---

## 4. Answer Submission APIs

### 4.1 Submit Answer
```
POST /evaluation/submit
```

**Allowed State**: `ANSWER_SUBMITTED`

**Request**
```json
{
  "question_id": "uuid",
  "answer_type": "VIDEO | TEXT | CODE",
  "answer_payload": "string"
}
```

**Response**
```json
{
  "state": "EVALUATING"
}
```

---

## 5. Coding Interview APIs

### 5.1 Fetch Coding Template
```
GET /code/template/{question_id}
```

**Allowed State**: `IN_PROGRESS`

**Response**
```json
{
  "language": "python",
  "starter_code": "string"
}
```

---

## 6. Conversational Interview APIs

### 6.1 Fetch Conversational Prompt
```
GET /conversation/prompt
```

**Allowed State**: `IN_PROGRESS`

**Response**
```json
{
  "prompt": "string",
  "followup_allowed": true
}
```

---

## 7. Proctoring APIs (REST)

### 7.1 Report Proctoring Event
```
POST /proctoring/event
```

**Allowed State**: `IN_PROGRESS`

**Request**
```json
{
  "event_type": "TAB_SWITCH | MULTI_FACE | VOICE_MISMATCH",
  "confidence": 0.92
}
```

**Response**
```json
{
  "action": "IGNORE | FLAG | TERMINATE"
}
```

---

## 8. Interview Summary & Reporting

### 8.1 Fetch Interview Summary
```
GET /summary
```

**Allowed State**: `COMPLETED | TERMINATED`

**Response**
```json
{
  "final_score": 78,
  "recommendation": "PROCEED",
  "fraud_risk": "LOW",
  "strengths": ["string"],
  "gaps": ["string"],
  "notes": "string"
}
```

---

## 9. Zwayam Integration APIs

### 9.1 Push Final Decision to Zwayam
```
POST /zwayam/push-feedback
```

**Allowed State**: `COMPLETED | TERMINATED`

**Request**
```json
{
  "decision": "PROCEED | HOLD | REJECT",
  "final_score": 78,
  "fraud_summary": "string"
}
```

**Response**
```json
{
  "status": "SYNCED"
}
```

---

## 10. State Enforcement Rules

- Every endpoint must validate current interview state
- Invalid transitions return `INVALID_STATE`
- State transitions occur **only on backend**

---

## 11. Change Policy

Any modification to this document requires:
- Interview State Machine review
- Frontend API impact validation
- Zwayam integration confirmation

