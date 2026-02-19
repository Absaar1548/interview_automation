# AI Coding Rules (Strict)

When generating code:

## General
- No demo or tutorial-style code
- No excessive comments
- Code should look production-ready
- Prefer clarity over cleverness

## Frontend
- Use Next.js App Router
- Use TypeScript everywhere
- Components should be small and composable
- Business logic must NOT live in components
- WebSocket logic must be isolated in lib/

## Backend
- FastAPI with async endpoints
- No global state
- Services must be stateless
- Use explicit schemas (Pydantic)
- WebSocket handling must be robust (disconnects, heartbeats)

## Architecture
- Do not mix layers
- No circular imports
- Follow folder responsibility strictly
