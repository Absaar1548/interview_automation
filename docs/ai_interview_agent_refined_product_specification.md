# AI Interview Agent – Product Specification (Refined)

## 1. Objective
Design a **low‑cost, high‑accuracy (≥90%) AI‑powered interview agent** tightly integrated with **Zwayam**, enabling end‑to‑end automation from interview initiation to structured feedback closure, with strong fraud detection and decision support for RR Owners and Delivery Heads.

---

## 2. Scope & Assumptions
- **Primary users**: Talent Acquisition (TA), Candidates, RR Owner, Delivery Head (DH)
- **Interview mode**: Video + Written Q&A
- **Architecture philosophy**: Cost‑first, API‑driven AI (no heavy custom model training in Phase 1)
- **Governance**: Human‑in‑the‑loop enabled from Day 1 for validation, overrides, and learning

---

## 3. End‑to‑End User Journey (Zwayam Integrated)
1. TA initiates interview from Zwayam.
2. Candidate receives a Zwayam‑generated interview link (valid for 48 hours).
3. Candidate completes AI‑led interview (video + written).
4. AI performs real‑time assessment with silent fraud checks.
5. Auto‑generated feedback, transcript, and fraud summary are shared with RR Owner & DH.
6. Delivery Head reviews and approves/rejects.
7. Approved feedback is pushed back to Zwayam with mandatory fields.
8. Interview status marked **Closed** in Zwayam.

---

## 4. Functional Requirements (Interview Agent)

### 4.1 Workflow & Integration
- Seamless launch from Zwayam interview link
- No separate candidate login (magic link access)
- Bi‑directional status, feedback, and metadata sync with Zwayam

### 4.2 Question Bank Management
- Role‑based question banks (predefined or AI‑generated)
- Skills mapped from RR discussion with Delivery Head
- Adaptive branching based on candidate responses

### 4.3 Capability Assessment
- Linguistic proficiency scoring (grammar, fluency, clarity)
- Tuned specifically for Indian English
- JD–Candidate alignment using semantic similarity
- Skill‑depth scoring per competency

### 4.4 Fraud Detection (Silent Background Execution)
- Face and voice match against live feed
- Liveness detection and spoof/deepfake signals
- Plagiarism and AI‑generated answer detection
- Behavioral anomalies (hesitation, response latency, typing patterns)
- CV vs interview vs public‑profile coherence checks

### 4.5 Compensation & Intent Analysis
Automated capture and analysis of:
- Compensation expectations
- Notice period
- Intent and sentiment
- Drop‑off / attrition risk indicators

### 4.6 Joining Date Confidence
- Explicit joining‑date capture
- Clarification follow‑ups on ambiguity
- Joining confidence score derived from behavioral and historical cues

### 4.7 Interview Orchestration & Experience
- Adaptive questioning (video + text)
- Human‑in‑the‑loop shadow mode (feedback correction)
- Unified HR dashboard
- Full audit trail and monitoring

---

## 5. Non‑Functional Requirements
- **Accuracy**: ≥90% selection relevance
- **Latency**: Near real‑time scoring and fraud signals
- **Security**: PII masking, encrypted storage
- **Scalability**: API‑first, cloud‑native
- **Cost**: Preference for usage‑based, commodity AI models

---

## 6. Requirements Backlog & Feedback Loops

### 6.1 Client Feedback Analysis & Continuous Improvement
- Collect structured feedback on assessment quality and overall tool experience
- Implement a decoupled feedback analysis module to detect trends and recurring issues
- Surface actionable insights for asynchronous application improvements
- Apply iterative UX and workflow enhancements **without direct reinforcement learning** to ensure system stability

### 6.2 Candidate Joining Confirmation & Score Validation
- Implement post‑offer joining confirmation tracking
- Use joining outcomes as a feedback loop to validate joining confidence scores
- Measure predictive accuracy over time and recalibrate heuristics

---

## 7. Requirements Traceability Matrix (TBU by Technical Team)

| Requirement | AI Model / API Used | Cost (Indicative) | Benefit Achieved | Accuracy Achieved |
|------------|--------------------|------------------|------------------|------------------|
| Linguistic proficiency scoring | GPT‑4o / Azure OpenAI | Low | Objective communication scoring | 92–94% |
| JD–skill alignment | Sentence Transformers / Embeddings | Very Low | Role‑fit precision | 90–92% |
| Adaptive questioning | LLM + Rules Engine | Low | Deeper skill validation | 90%+ |
| Face & voice verification | Azure Face + Speaker Recognition | Medium | Identity assurance | ~95% |
| Liveness & deepfake detection | Azure Vision + Audio Spoof Models | Medium | Impersonation risk reduction | 93–95% |
| Plagiarism / AI‑answer detection | Text similarity + classifiers | Low | Response integrity | 90–92% |
| Behavioral anomaly detection | Heuristics + ML | Very Low | Fraud signal enrichment | ~90% |
| CV ↔ profile ↔ interview coherence | Embeddings + rules | Low | Data trustworthiness | 91–93% |
| Compensation & intent extraction | LLM + sentiment models | Low | Early drop‑off risk detection | ~90% |
| Joining date confidence | LLM + heuristics | Very Low | Joining predictability | 90–91% |
| Unified dashboard & audit | BI + metadata logs | Low | Decision transparency | N/A |

---

## 8. Cost Optimization Strategy
- Prefer API‑based foundation models (Phase 1)
- Batch embedding generation
- Human review only for low‑confidence cases
- Phase 2: selective fine‑tuning for high‑volume roles

---

## 9. Success Metrics
- ≥90% correlation with human interviewer decisions
- ≥30% reduction in TA effort
- ≥25% faster interview‑to‑closure cycle
- <5% false‑positive fraud flags

---

## 10. High‑Level Architecture
- Modular monolithic backend (single deployable unit for Phase 1)
- Event‑driven internal workflows for scoring, fraud alerts, and reporting
- REST APIs + WebSockets for session control and real‑time proctoring
- API‑first, cloud‑native, cost‑optimized Azure deployment

### 10.1 Frontend
- Web application (React / Next.js)
- Magic‑link access (Zwayam‑initiated)
- Secure browser enforcement (fullscreen, clipboard restriction, tab‑switch detection)
- Media capture: video, audio, and text streaming

### 10.2 Backend
- Python (FastAPI) monolithic backend with logically separated modules
- Hosted on Azure with managed compute, storage, and databases
- Lightweight gateways for LLMs, Vision, Speech, and embeddings

---

## 11. Core Logical Components

### 11.1 Interview Orchestration & AI‑Driven Questioning
- Controls interview lifecycle (start, progression, termination, resume logic)
- Adaptive question flow with difficulty balancing (30/40/30)
- Questions sourced from role‑ and skill‑specific banks
- Delivery Head / Manager question inputs supported
- Contextual rephrasing using JD, resume, and previous answers
- Conversational follow‑ups for depth and clarification
- Streams prompts, timers, and guidance to frontend

### 11.2 Resume Parser & Profile Analyzer
- Extracts skills, experience, seniority, projects, and LinkedIn
- Normalizes resumes into structured candidate profiles
- Feeds JD‑candidate alignment and question personalization

### 11.3 Proctoring & Fraud Detection Service
- Browser‑level enforcement (fullscreen, tab‑switch, clipboard)
- AI‑based proctoring:
  - Face and voice match
  - Liveness and spoof detection
  - Multiple‑person detection
  - Whisper/background voice detection
  - Behavioral anomaly tracking
- Computes cheat score with soft vs hard violation flags

### 11.4 Scoring, Evaluation & Reporting
- Evaluates spoken, written, and video responses using:
  - LLM reasoning
  - Skill‑depth scoring
  - JD alignment
  - Linguistic proficiency
- Applies plagiarism thresholds and cheat‑score penalties
- Generates structured feedback, transcript, and fraud summary
- Provides explainability: strengths, gaps, risks
- Stores metadata and reports; enforces media retention policies

### 11.5 Zwayam Integration Gateway
- Initiates interviews using RR, JD, and candidate metadata
- Pushes approved feedback and final decision to Zwayam
- Manages interview state transitions
- Webhook‑based bi‑directional synchronization

