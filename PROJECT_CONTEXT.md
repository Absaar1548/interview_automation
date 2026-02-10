# Interview Automation System – Project Context

This is an AI-driven L1 Interview Automation System.

## High-level goals
- Fully automated technical screening interviews
- Conversational AI interviewer
- Resume-aware question selection
- Real-time proctoring (audio + video)
- Explainable scoring & reports

## Tech Stack
Frontend:
- Next.js (App Router)
- TypeScript
- Tailwind CSS
- WebSockets for live interview

Backend:
- Python
- FastAPI
- REST + WebSockets
- Monolithic deployment with modular services

## Architectural principles
- Frontend-first UX-driven development
- Contract-first APIs
- Clear separation of concerns
- No premature microservices
- Readable, production-grade code (not demo code)

## Key backend components
- Interview Orchestrator (state machine)
- Question Engine
- Proctoring Service
- Evaluation & Scoring
- Reporting

## Constraints
- Low scale initially
- English only
- Single LLM (multiple prompts)
- Azure infrastructure (later)

All code should follow these principles strictly.
