# AI Interview Agent – Project Context

This system is a low-cost, high-accuracy AI-powered L1 interview agent
integrated with Zwayam.

## Core goals
- End-to-end interview automation
- ≥90% selection relevance
- Strong fraud detection with low false positives
- Structured, explainable feedback for RR Owners and Delivery Heads

## Architecture
- Modular monolithic backend (FastAPI)
- Next.js frontend
- REST APIs + WebSockets
- Event-driven internal workflows
- API-first, cost-optimized design

## Key capabilities
- Video + written interviews
- Adaptive questioning (30/40/30 difficulty)
- Resume & JD-aware personalization
- Silent fraud detection (face, voice, behavior)
- Human-in-the-loop validation
- Zwayam bi-directional integration

## Constraints
- No heavy model training in Phase 1
- Prefer API-based AI models
- English only
- Azure-first deployment


## Development Environment
- **Mock Backend**: Located in `mock_backend/`. Use this for development until full backend integration.
- **Frontend**: Located in `frontend/`. Connects to `localhost:8000`.

All generated code must:
- Be production-grade
- Follow the defined folder responsibilities
- Avoid over-engineering
