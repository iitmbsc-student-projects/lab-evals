# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Full-stack app for managing **offline lab evaluations** at an institution. Roles are **per lab session**, not global: a user can be a `student` on one session and a `ta` on another. `is_admin: bool` on `User` is the only global privilege. TAs evaluate students on per-subject questions (1–5 marking + remarks); admins manage subjects, questions, lab sessions, session rosters, users, and the audit log.

- **Backend**: FastAPI + SQLAlchemy 2.0 (Python 3.13, `uv`), in `backend/`
- **Frontend**: Vue 3 + Vite + Pinia + vue-router + Tailwind v4 (TypeScript, `bun`), in `frontend/`
- **Deploy**: Cloud Run (backend) + Firebase Hosting (frontend) + Cloud SQL Postgres + Secret Manager, region `asia-south1`. See `deploy/SETUP.md`.

## Commands

Both subprojects expose the same verbs through a `Makefile`. Run from repo root with `-C`, or `cd` in.

```bash
# Backend (uv)
make -C backend install     # uv sync
make -C backend run         # uvicorn app.main:app --reload on :8000
make -C backend check       # ruff format + ruff check --fix  (run before committing)
make -C backend up          # docker compose (local containerized run)

# Frontend (bun)
make -C frontend install    # bun install
make -C frontend run        # vite dev server on :5173
make -C frontend type-check # vue-tsc --build  (TS errors live here, not in `run`)
make -C frontend lint        # eslint --fix
make -C frontend build      # type-check + vite build  (build fails on type errors)

# Deploy (one-time GCP setup in deploy/SETUP.md must be done first)
make -C backend deploy       # gcloud builds submit --config=cloudbuild.yaml
make -C frontend deploy
```

There are **no tests** in this repo. There is no test runner configured — don't assume `pytest`/`vitest` exist.

Both projects default to working without a `.env` (sqlite + dummy secrets on the backend); copy `*/.env.example` to `*/.env` for real config.

## Architecture

### Auth: Google-only, pre-enrollment required

No passwords. Flow: frontend renders Google Identity Services button (`src/auth/google.ts`) → gets an `id_token` → `POST /api/v1/auth/login` → backend verifies the token with Google (`core/auth.py`), then **looks up an existing user** by `google_sub`, falling back to `email`. There is **no self-signup**: if the email isn't already in the `users` table, login fails with "User not enrolled". On first login `google_sub` is bound to the pre-enrolled email row. The backend then issues its own JWT (HS256, payload `{user_id}` only — role is now per-session, resolved at request time).

The **admin user is auto-created on startup** from `ADMIN_EMAIL`/`ADMIN_NAME` (lifespan in `main.py`) with `is_admin=True`. That's the bootstrap account; everyone else is created by an admin via `/api/v1/admin/users`.

### RBAC is enforced at the router level

Two layers of authorization:

1. **Admin router** (`api/v1/admin.py`) is gated whole-cloth by `require_admin` (`api/deps.py`), which checks `User.is_admin`. Every endpoint in that file requires global admin — no mixing.

2. **TA/student endpoints** (`api/v1/sessions.py` and related) authorize per request via context checks: `is_ta_on_session(db, user_id, session_id)` / `is_student_on_session(db, user_id, session_id)`. A user's role on a session is resolved from `SessionAssignment` at request time.

**`accepting_evaluations` gate:** TA create/edit/delete of evaluations requires the session's `accepting_evaluations=True`; reads (list/get) are always allowed. Students see only the _presence_ of their evaluations (submitted/not), never marks or remarks.

The frontend is a **single unified portal**: `/` lists "my sessions" with role badges; `/sessions/:id` renders a TA grading view or a student presence view depending on the user's role on that session. There are no longer three separate layouts — the old `AdminLayout`/`TALayout`/`StudentLayout` split is gone; the admin area is a separate `/admin/*` section. Token lives in `localStorage` via the Pinia `auth` store; the axios client (`api/client.ts`) injects `Bearer` and hard-redirects to `/login` on any 401.

### Audit logging — read this before touching a mutating endpoint

Mutations are audited through `AuditRecorder` (`core/audit.py`). The critical contract: **`audit.record()` only stages the row with `db.add()` — it does NOT commit.** The route handler owns the `db.commit()`, so the audit row and the business mutation share one transaction (both commit or both roll back; no orphan audit entries). The established pattern in `ta.py`/`admin.py` is:

```python
db.add(obj); db.flush()           # flush to get obj.id
audit.record(db, action="...", resource_type="...", resource_id=obj.id,
             request_body=..., before_state=snapshot(old), after_state=snapshot(obj))
db.commit()
```

`snapshot(db_obj)` serializes a model row to a JSON-safe dict (datetime→ISO, Enum→.value) for before/after diffs.

### DB sessions are managed manually, not via DI

Handlers do `db = SessionLocal()` inside `try/.../finally: db.close()` — they do **not** use a FastAPI dependency for the session. Follow this pattern in new endpoints rather than introducing a `get_db` dependency.

### No migrations — schema is create-only on startup

`Base.metadata.create_all()` runs in the `main.py` lifespan. New tables/columns appear on the next (cold) start. **Destructive changes (drops, type changes, renames) are NOT handled** — they need a manual `ALTER` against the DB. There is no Alembic. Keep model changes additive unless you also plan the manual migration.

**One-time reset for the per-session RBAC migration:** The switch from global roles to per-session roles removed `enrollments`, added `is_admin` to `users`, restructured `evaluations`, and introduced `lab_sessions`/`session_assignments`. On **existing** databases you must do a one-time reset before starting the new server:
- _Local (SQLite)_: `rm backend/dev.db` — cold start recreates everything.
- _Cloud SQL (Postgres)_: `DROP TABLE enrollments, evaluations, users CASCADE;` then let the next cold start recreate them. `lab_sessions` and `session_assignments` are new and will be created automatically.

### Layering

`api/v1/*` (role-gated routers, where the business logic actually lives) → `models/*` (SQLAlchemy) + `schemas/*` (Pydantic). The `services/*` modules exist but are essentially empty placeholders — **do not assume logic lives in services**; it's in the routers today. Key routers: `admin.py` (global-admin gated), `sessions.py` (per-session authz for TA/student actions). Schemas are context-specific (e.g. `TAEvaluationCreate`, `StudentEvaluationPresence`), and the frontend's `src/api/*.ts` + `src/types/api.ts` mirror the backend route groups.

### Data model

`User` (`is_admin: bool`); `Subject` —< `Question`; `Subject` —< `LabSession(date, accepting_evaluations)` UNIQUE(subject, date) —< `SessionAssignment(role: student|ta)` UNIQUE(session, user) — this roster IS the membership; `Evaluation(lab_session, student, question, ta, marking 1–5, remarks)` UNIQUE(lab_session, student, question); `AuditLog` is append-only. There is no `Enrollment` table.

## Conventions

- **Backend lint/format**: ruff, **line length 79**, double quotes, `target-version py313`. Run `make -C backend check` before committing.
- **Frontend**: ESLint + Prettier; type errors surface via `vue-tsc` (`type-check`/`build`), not the dev server.
- **Config** (`core/config.py`): plain `Settings` class reading `os.getenv` with dev defaults, `@lru_cache`d. `ENV=development` turns on CORS `*` and SQL echo; production sets CORS to `FRONTEND_ORIGIN` only. `DATABASE_URL` is sqlite locally, Postgres (`postgresql+psycopg://`) in prod.
- **Secrets in prod** come from Secret Manager via Cloud Run `--set-secrets`; the frontend bakes `VITE_*` at build time. The repo is split-deployable — `cloudbuild.yaml` per subproject, with GitHub triggers filtered by path so backend/frontend changes deploy independently.
