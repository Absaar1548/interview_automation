# Interview System File Summary

This document provides a detailed summary of the key frontend and backend files involved in the AI Interview System.

## Frontend (Critical)

### 1. `src/store/interviewStore.ts`
**Purpose:** Central state management using `zustand`.
**Key State:**
- `interviewId`, `candidateToken`: Session credentials.
- `state`: Current interview state (e.g., `READY`, `IN_PROGRESS`, `EVALUATING`).
- `currentQuestion`: The active question object.
- `isConnected`: WebSocket connection status.
**Key Actions:**
- `initialize`: Sets credentials and sets up `interviewService` callbacks.
- `startInterview`: Calls API to start session.
- `fetchNextQuestion`: Retrieves the next question.
- `submitAnswer`: Submits answer and handles state transition.
- `terminate`: Clears state and stops services.

### 2. `src/lib/interviewService.ts`
**Purpose:** Singleton service layer acting as a bridge between the Store, API, and WebSockets.
**Key Responsibilities:**
- Manages lifecycle of `controlWebSocket` and `proctoringEngine`.
- Provides methods for API calls: `startInterview`, `fetchNextQuestion`, `submitAnswer`.
- Handles `onConnected`, `onTerminated`, `onError` callbacks from the store.

### 3. `src/lib/controlWebSocket.ts`
**Purpose:** Manages the signaling WebSocket connection (`/api/v1/proctoring/ws`).
**Key Features:**
- **Handshake:** Sends `interview_id` and `candidate_token` on connection.
- **Heartbeat:** Sends periodic `HEARTBEAT` messages (default 10s) to keep connection alive and validate session state.
- **Handling Messages:** Listens for `TERMINATE` signals from backend (e.g., due to fraud).

### 4. `src/lib/mediaWebSocket.ts`
**Purpose:** Manages the media streaming WebSocket (`/api/v1/proctoring/media/ws`).
**Key Features:**
- **Streaming:** Sends partial binary data (ArrayBuffer) from `MediaRecorder`.
- **Reconnection:** Implements auto-reconnect logic (up to 3 attempts).
- **One-way:** Primarily sends data; backend ignores incoming messages in this mock version.

### 5. `src/lib/answerWebSocket.ts`
**Purpose:** Manages real-time audio answer streaming and transcription (`/api/v1/answer/ws`).
**Key Features:**
- **Flow:** `START_ANSWER` -> Stream Audio -> `END_ANSWER` -> `TRANSCRIPT_FINAL` -> `ANSWER_READY`.
- **Events:** Dispatches `onPartialTranscript`, `onFinalTranscript`, and `onAnswerReady` callbacks.

### 6. `src/lib/proctoringEngine.ts`
**Purpose:** Controls the browser's `MediaRecorder` API.
**Key Features:**
- **Capture:** Requests camera/microphone access (`getUserMedia`).
- **Processing:** Slices media into chunks (1000ms) and sends them via `mediaWebSocket`.
- **Lifecycle:** `start()`/`stop()` methods ensuring resources (tracks) are released.

### 7. `src/components/interview/InterviewShell.tsx`
**Purpose:** The main container component for the active interview interface.
**Key Features:**
- **Orchestration:** Renders `Timer`, `QuestionPanel`, and `AnswerPanel`.
- **Logic:** Handles answer submission (manual or timer-expired).
- **State Guard:** Returns `null` if state is not `QUESTION_ASKED`.

### 8. `src/components/interview/AnswerPanel.tsx`
**Purpose:** UI for inputting answers.
**Key Features:**
- **Modes:** Supports `AUDIO` (recording) and `CODE` (text area) modes.
- **Audio Logic:** Manages local `MediaRecorder` for answers, connects to `answerWebSocket` to stream audio and display live transcripts.
- **Feedback:** Shows recording status and final transcript/ID.

### 9. `src/components/interview/QuestionPanel.tsx`
**Purpose:** Display component for the current question.
**Key Features:**
- Shows: Category, Difficulty, Answer Mode, and the main Prompt.
- Styling: Uses Tailwind classes for badges and layout.

### 10. `src/components/interview/Timer.tsx`
**Purpose:** Countdown timer component.
**Key Features:**
- **Props:** `durationSec`, `onExpire`.
- **Logic:** Decrements every second. Triggers `onExpire` callback when reaching 0. Includes cleanup on unmount.

### 11. `src/app/interview/page.tsx`
**Purpose:** The Next.js page entry point for `/interview`.
**Key Features:**
- **Bootstrap (Dev):** In development mode, auto-fetches credentials from `/api/v1/dev/bootstrap` if missing.
- **Routing/Guards:** Redirects or shows errors if session is invalid or terminated.
- **Rendering:** Renders `InterviewShell` when active, or completion/termination screens.

### 12. `src/types/api.ts`
**Purpose:** Shared TypeScript types defining the API contract.
**Key Types:**
- `InterviewState`: Enum of valid states (`CREATED` -> `TERMINATED`).
- `QuestionResponse`: Structure of question objects.
- `WebSocket` Messages: Protocols for handshake and events.

---

## Backend (Mock Core & Endpoints)

### 1. Mock Core Architecture (Critical Context)
- **`mock_backend/interview_store.py`**:
  - **In-Memory Storage:** Uses a global `INTERVIEWS` dictionary to store session state.
  - **Logic:** Handles creation, retrieval, state transitions, and cheat score accumulation.
- **`mock_backend/state_machine.py`**:
  - **Definitions:** Defines `InterviewState` enum and `VALID_TRANSITIONS` map.
  - **Validation:** Ensures transitions (e.g., `READY` -> `IN_PROGRESS`) are valid.
- **`mock_backend/mock_question_bank.py`**:
  - **Data:** Returns a fixed list of 4 questions covering Conversational, Static, and Coding categories.
- **`mock_backend/mock_evaluation.py`**:
  - **Logic:** "Simulates" AI evaluation. Deterministically advances question index or completes the interview if it's the last question.

### 2. `api/v1/endpoints/proctoring_router.py`
**Purpose:** Handles proctoring logic.
**Key Endpoints:**
- `POST /event`: Receives client-side events (e.g., TAB_SWITCH). Terminates on hard violations.
- `WS /ws`: Signaling WebSocket. Validates handshake, handles heartbeats, checks for server-side termination.
- `WS /media/ws`: Dummy endpoint to accept media streams (currently discards data).

### 3. `api/v1/endpoints/answer_router.py`
**Purpose:** Handles answer processing.
**Key Endpoints:**
- `WS /ws`: Answer WebSocket. Accepts `START_ANSWER`, audio streams (ignored), and `END_ANSWER`.
- **Mock Response:** Returns a static "This is a mock final transcription" and a generated `transcript_id` upon completion.

### 4. `api/v1/endpoints/submit_evaluation_router.py`
**Purpose:** Submitting answers for evaluation.
**Key Endpoints:**
- `POST /submit`: Accepts `answer_payload`, transitions state, triggers mock evaluation (simulating delay and scoring), and returns updated state.

### 5. `api/v1/endpoints/question_router.py`
**Purpose:** Question retrieval.
**Key Endpoints:**
- `GET /next`: Returns the next question from the mock store based on the current session index.

### 6. `api/v1/endpoints/dev_router.py`
**Purpose:** Development utilities.
**Key Endpoints:**
- `GET /bootstrap`: Creates a new session with fixed token `dev-candidate-token`, fast-forwards it to `READY` state, and returns credentials.
