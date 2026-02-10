# Interview State Machine (Authoritative)

This document defines the **authoritative interview lifecycle state machine** for the AI Interview Agent backend.

This state machine is **contractual** between:
- Frontend (Next.js)
- Backend (FastAPI)
- Proctoring & evaluation subsystems
- Zwayam integration

Any change to this document requires explicit review.

---

## 1. Design Principles

- Single active interview per candidate
- Deterministic state transitions (no ambiguity)
- State-driven API behavior
- Failure-safe termination
- Human-in-the-loop hooks at defined checkpoints

---

## 2. State Definitions

### 2.1 CREATED
**Meaning**: Interview entity created but not yet started.

**Entry Conditions**:
- Zwayam initiates interview
- Magic link generated

**Allowed Actions**:
- Resume upload
- JD & RR metadata ingestion

**Exit Conditions**:
- Resume successfully parsed

**Next State**: `RESUME_PARSED`

---

### 2.2 RESUME_PARSED
**Meaning**: Candidate resume and JD processed.

**Actions Performed**:
- Skill extraction
- Seniority estimation
- JD–resume alignment

**Allowed Actions**:
- Question pool preparation

**Next State**: `READY`

---

### 2.3 READY
**Meaning**: Interview is fully prepared and waiting to start.

**Entry Conditions**:
- Candidate opens interview link
- Browser & media permissions validated

**Allowed Actions**:
- Frontend handshake
- Proctoring initialization

**Next State**:
- `IN_PROGRESS`

---

### 2.4 IN_PROGRESS
**Meaning**: Interview actively running.

**Sub-States (Logical)**:
- QUESTION_ASKED
- ANSWER_COLLECTING
- EVALUATING

**Actions Performed**:
- Question delivery
- Video/audio capture
- Proctoring monitoring

**Transitions**:
- Normal flow → next QUESTION_ASKED
- Hard violation → `TERMINATED`

---

### 2.5 QUESTION_ASKED
**Meaning**: A question has been delivered to candidate.

**Constraints**:
- Only one active question at a time

**Next State**:
- `ANSWER_SUBMITTED`

---

### 2.6 ANSWER_SUBMITTED
**Meaning**: Candidate submitted response.

**Actions**:
- Freeze answer
- Trigger evaluation

**Next State**:
- `EVALUATING`

---

### 2.7 EVALUATING
**Meaning**: Backend evaluating answer.

**Actions**:
- LLM scoring
- Coding execution
- Fraud signal aggregation

**Next State**:
- `IN_PROGRESS` (next question)
- `COMPLETED` (if interview finished)

---

### 2.8 COMPLETED
**Meaning**: Interview completed successfully.

**Actions**:
- Final scoring
- Report generation
- Zwayam feedback push

**Terminal State**

---

### 2.9 TERMINATED
**Meaning**: Interview forcibly ended.

**Causes**:
- Hard fraud violation
- System abuse
- Explicit admin termination

**Actions**:
- Mark interview failed
- Generate partial report
- Push termination reason to Zwayam

**Terminal State**

---

## 3. Violation Handling Rules

### Hard Violations
- Multiple faces detected
- Voice mismatch
- Explicit impersonation

→ Immediate transition to `TERMINATED`

### Soft Violations
- Looking away frequently
- Background noise
- Suspicious pauses

→ Accumulate cheat score (no state change)

---

## 4. Human-in-the-Loop Hooks

| State | Hook | Purpose |
|------|------|--------|
| EVALUATING | Feedback override | Score correction |
| COMPLETED | Approval | Push to Zwayam |
| TERMINATED | Review | False positive audit |

---

## 5. State Transition Summary

```
CREATED
  ↓
RESUME_PARSED
  ↓
READY
  ↓
IN_PROGRESS
  ↓
QUESTION_ASKED
  ↓
ANSWER_SUBMITTED
  ↓
EVALUATING
  ↓
IN_PROGRESS | COMPLETED

(Hard violation → TERMINATED)
```

---

## 6. Enforcement Rules

- APIs must validate current state before execution
- Frontend must treat state as source of truth
- WebSocket events are state-scoped

---

## 7. Change Policy

This document is authoritative.

Any change requires:
- Frontend impact review
- Zwayam contract validation
- Proctoring impact assessment
