<!-- Copilot instructions for this repository. Keep short and specific. -->
# Copilot / AI Agent Instructions

Purpose: Help an AI agent become productive quickly in this FastAPI + SQLAlchemy project.

- Quick run (development):
  - From repository root run: `uvicorn app.main:app --reload` (the repo README shows a similar command).

- Big picture:
  - Backend: FastAPI app under `app/` with routers in `app/api/*.py`. Main entry is `app/main.py`.
  - Database: SQLAlchemy ORM models live in `app/Models/`. DB session is configured in `app/db/session.py` (hard-coded `DATABASE_URL`). Migrations are under `alembic/`.
  - Auth: JWT-based in `app/core/security.py`; token creation/decoding uses hard-coded `SECRET_KEY` and custom claim names. Current user logic is in `app/api/deps.py`.
  - Features: background sync and device integration code under `app/features/` (Hikvision/Dahua integrations in `app/features/RecordInfo` and `app/features/sync`). These call external camera APIs and populate `ChannelRecordDay` and `ChannelRecordTimeRange` models.
  - Frontend: static files in `wwwroot/` (HTML + JS call backend at `/api/*`). CORS is allowed (`allow_origins=['*']`) in `app/main.py`.

- Developer workflows & commands to know:
  - Run dev server: `uvicorn app.main:app --reload` (port 8000 default).
  - DB migrations: use `alembic` from project root. Example: `alembic revision --autogenerate -m "msg"` then `alembic upgrade head`.
  - If enabling background worker, switch `app/main.py` to use the `lifespan` context manager (it's present but commented out) so `sync_background_worker()` is started.

- Project-specific patterns and pitfalls:
  - Many endpoints depend on `get_current_user` which extracts custom JWT claim URIs; tokens must include these claims. See `app/core/security.py` and `app/api/deps.py`.
  - DB connection is defined in `app/db/session.py` with a hard-coded URL — change for local vs prod.
  - Several services (HikRecordService, Dahua code) are asynchronous and perform network I/O; treat them as potentially slow and add timeouts/retries when modifying.
  - Frontend JS expects endpoints like `/api/devices`, `/api/devices/{id}/channels`, `/api/devices/channels/{channel_id}/record_days_full` — mirror these paths when adding APIs.

- Key files to inspect when making changes:
  - `app/main.py` — app lifecycle, CORS, background worker
  - `app/routers.py` and `app/api/*.py` — API surface
  - `app/db/session.py`, `app/db/base.py` — DB engine and model base
  - `app/Models/*` and `app/schemas/*` — ORM models and pydantic schemas
  - `app/features/RecordInfo/*` — camera record retrieval and merging logic
  - `wwwroot/` — static UI, the JS there calls backend APIs directly

- Safety & practical constraints for the agent:
  - Do not change `SECRET_KEY` without instruction; note it's currently checked into source (security risk). Document changes instead of secretly rotating it.
  - Avoid expensive sync operations by default (calls under `/get_channels_record_info`); warn before invoking.

- Example short tasks (how to implement):
  - Add a new API route: update `app/api/<module>.py`, add schema in `app/schemas/`, and model in `app/Models/` if needed; write DB logic using `get_db()` dependency and `get_current_user()` when auth is required.
  - Preview frontend changes: open `wwwroot/<file>.html` in browser or run a simple static server (e.g. `python -m http.server 5500` inside `wwwroot/`) while backend runs on port 8000.

If anything is unclear or you want the agent to follow stricter coding rules (type hints, tests, formatting), tell me which conventions to enforce and I will update this file.
