# AGENTS.md

always keep this file updated. minimal text.

## Project
FastAPI + Firebase Authentication backend for VerifAI.

## Stack
- Python 3.x, FastAPI
- Firebase Admin SDK (email/password auth)
- Bearer token auth on protected routes

## Code Style
- No inline comments
- Keep files minimal
- Clean layered architecture

## Commands
- Run: `uvicorn main:app --reload`
- Lint: `ruff check .`
- Format: `ruff format .`
- Test: `pytest tests/ -v`
- Test watch: `pytest tests/ -v --looponfail`

## Structure
```
main.py                      # Entry point — creates FastAPI app, includes routers
app/
  core/
    config.py                # Settings, env, Firebase init
    security.py              # HTTPBearer dependency, token verification
  schemas/
    auth.py                  # Pydantic request/response models
  api/v1/
    auth.py                  # Route handlers (thin — delegates to services)
  services/
    auth_service.py          # Business logic layer
  repositories/
    firebase_repository.py   # Firebase Admin + REST data access
firebase-key.json            # Service account key (gitignored)
```
