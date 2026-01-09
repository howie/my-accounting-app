---
description: Restart all services (backend, frontend) for manual testing
---

## Manual Test Environment Setup

Restart backend and frontend services for manual testing.

## Steps

1. **Kill existing processes**: Stop any running uvicorn (backend) and next dev (frontend) processes.

2. **Start Backend**:
   - Directory: `backend/`
   - Activate virtualenv: `source .venv/bin/activate`
   - Command: `uvicorn src.main:app --reload --port 8000`
   - Run in background

3. **Start Frontend**:
   - Directory: `frontend/`
   - Command: `npm run dev`
   - Run in background

4. **Health Check**: Wait for services to be ready, then verify:
   - Backend: `curl http://localhost:8000/health`
   - Frontend: `curl http://localhost:3000`

5. **Report URLs**:
   | Service | URL |
   |---------|-----|
   | Frontend | http://localhost:3000 |
   | Backend API | http://localhost:8000 |
   | API Docs | http://localhost:8000/docs |
