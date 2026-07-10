# Ethara Seat Allocation & Project Mapping System

A full-stack internal tool for managing seat allocation and project mapping for a ~5,000-employee organization. Built for the Ethara technical assessment.

> **Note on the spec:** the detailed assessment document (business rules, exact API contracts, submission guidelines) referenced in the assignment brief was not available during development. This build was implemented directly from the requirement list in the assignment prompt. Every place a business rule had to be *assumed* rather than specified is called out explicitly in [Business Rules & Assumptions](#business-rules--assumptions) below — check these against the real spec before treating this as final.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind CSS + Recharts |
| Backend | FastAPI (Python 3.12) |
| Database | PostgreSQL (SQLAlchemy 2.0 ORM) |
| AI Assistant | Rule-based NL parser + optional Claude API fallback |
| Deployment target | Railway/Render (backend + Postgres), Vercel/Netlify (frontend) |

## Features Implemented

- **Employee Management** — CRUD, department assignment, manager hierarchy, offboarding (soft-delete that auto-releases seat + ends project assignments)
- **Project Mapping** — projects, team assignments with role + allocation %, enforces that an employee's allocation across active projects can't exceed 100%
- **Seat Allocation & Release** — allocate/release with double-booking prevention, one-active-seat-per-employee rule, full allocation history per employee
- **New Joiner Seat Allocation** — creates the employee record and attempts immediate auto-allocation (floor+zone → floor → any available seat, in that priority order); falls back to a "pending" queue with a retry endpoint if nothing is free
- **Search & Filter** — per-entity filters (employee search/department/status/project/has-seat; seat floor/zone/type/occupancy; project search/status) plus one global search-everything endpoint
- **Dashboard & Analytics** — headcount, seat utilization (overall + per-floor), department headcount, top projects by headcount
- **AI Assistant / NL Query** — a chat box that answers questions like *"How many available seats on Floor 3?"* or *"Who sits at seat F2-C-012?"* (see [AI Assistant design](#ai-assistant-design) below)
- **REST API** — full CRUD + business-rule endpoints, documented via Swagger at `/docs`
- **Seed Data Generation** — one script generates ~5,000 employees, ~150 projects, ~5,200 seats across 5 floors, and realistic allocation/assignment data in a few seconds

## Project Structure

```
ethara/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, router registration
│   │   ├── database.py          # SQLAlchemy engine/session (PostgreSQL)
│   │   ├── models.py            # ORM models (8 tables)
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   ├── seed.py              # Seed data generator
│   │   └── routers/
│   │       ├── employees.py
│   │       ├── projects.py
│   │       ├── seats.py
│   │       ├── new_joiners.py
│   │       ├── dashboard.py
│   │       ├── search.py
│   │       └── assistant.py     # AI / NL query endpoint
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── app/                     # Next.js App Router pages
│   │   ├── page.tsx             # Dashboard
│   │   ├── employees/
│   │   ├── projects/
│   │   ├── seats/
│   │   ├── new-joiners/
│   │   └── assistant/
│   ├── components/
│   ├── lib/api.ts               # Typed API client
│   └── .env.local.example
├── database_schema.sql          # PostgreSQL DDL, generated from the SQLAlchemy models
├── AI_PROMPTS.md
└── README.md
```

## Local Setup

### Prerequisites
Python 3.11+, Node.js 18+, and PostgreSQL. The repository includes a Docker Compose service for local PostgreSQL.

### Quick Start (Windows)

```powershell
.\start-dev.ps1
```

This starts Docker/PostgreSQL, the backend on `http://127.0.0.1:8020`, and the frontend on `http://localhost:3000`.

### Backend

```bash
docker compose up -d postgres

cd backend
python3 -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# DATABASE_URL defaults to postgresql://ethara_user:ethara_pass@localhost:5432/ethara_db,
# matching the local Postgres service in docker-compose.yml.

# Generate seed data (drops and recreates all tables, then seeds ~5,000 employees)
python -m app.seed
# Smaller/faster dataset for quick iteration:
# SEED_EMPLOYEE_COUNT=300 python -m app.seed

uvicorn app.main:app --reload --port 8020
```

API is now live at `http://127.0.0.1:8020`, Swagger docs at `http://127.0.0.1:8020/docs`.

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # API_URL=http://127.0.0.1:8020
npm run dev
```

App is now live at `http://localhost:3000`.

## Environment Variables

**Backend (`backend/.env`)**
| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | Postgres connection string. The local default matches `docker-compose.yml`. |
| `GROQ_API_KEY` | No | Enables the Groq (Llama 3.3 70B) fallback for AI Assistant queries the rule-based parser can't classify. Free tier at [console.groq.com](https://console.groq.com). Assistant works without it. |
| `FRONTEND_ORIGINS` | No | Comma-separated CORS allowlist. Defaults to `http://localhost:3000`. |

**Frontend (`frontend/.env.local`)**
| Variable | Required | Description |
|---|---|---|
| `API_URL` | Yes for local dev | Backend API URL used by the Next.js `/api/*` proxy. Defaults to `http://127.0.0.1:8020` in `.env.local.example`. |
| `NEXT_PUBLIC_API_URL` | No | Optional public backend URL for deployments that should call the API directly from the browser. Leave unset for local dev. |

## API Documentation

Interactive Swagger UI is auto-generated by FastAPI at **`/docs`** (ReDoc at `/redoc`) on whatever host the backend is deployed to. Key endpoint groups:

| Prefix | Purpose |
|---|---|
| `/api/employees` | CRUD, search/filter, offboarding |
| `/api/projects` | CRUD, team roster, assignment create/end |
| `/api/seats` | List/filter, allocate, release, floors, per-employee history |
| `/api/new-joiners` | Create (with auto-allocation), list, retry allocation |
| `/api/dashboard` | Summary stats, utilization-by-floor, headcount breakdowns |
| `/api/search` | Cross-entity search (employees + seats + projects in one call) |
| `/api/assistant` | Natural-language query endpoint |

## Database Schema

See [`database_schema.sql`](./database_schema.sql) for the full PostgreSQL DDL. Summary:

- **departments** ← **employees** (department_id, self-referential `reporting_manager_id`)
- **employees** ↔ **projects** via **project_assignments** (many-to-many, with role + allocation % + active flag)
- **floors** → **seats** (one-to-many)
- **employees** ↔ **seats** via **seat_allocations** (history table — every allocate/release is a row, `status` = active/released, so "who sat where and when" is fully queryable)
- **new_joiner_requests** tracks the seat-request lifecycle for new hires (pending → allocated), separate from `seat_allocations` so the request itself has a record even before/if a seat is found

## Business Rules & Assumptions

No detailed spec was available, so the following were assumed and implemented — **verify these against the real requirements doc**:

1. An employee holds **at most one active seat** at a time; allocating a new one requires releasing the old one first.
2. A seat can be **actively allocated to only one employee** at a time (double-booking blocked with a 400).
3. An employee's **allocation % across active projects can't exceed 100%** (e.g. 60% + 60% is rejected).
4. **New joiner auto-allocation** priority: preferred floor + zone → preferred floor only → any available seat → stays "pending" if nothing's free.
5. **Offboarding** (`DELETE /api/employees/{id}`) is a soft-delete: marks the employee `exited`, releases their seat, and ends their active project assignments — it does not delete history.
6. Seats have a `seat_type` (regular / hot-desk / cabin) and an `is_active` flag for marking a seat under maintenance/decommissioned (excluded from availability).

## AI Assistant Design

The assistant does **not** let an LLM generate and execute raw SQL — on a system holding 5,000 employees' PII, that's an injection/data-exposure risk not worth taking. Instead:

1. A regex-based rule parser handles common question shapes locally (no API cost, zero latency beyond the DB query itself): available seats by floor, floor utilization, project/department headcount, who sits where, an employee's current seat, pending new joiners, total available seats, unseated employee count.
2. If a query doesn't match any rule **and** `GROQ_API_KEY` is set, it's sent to Groq (Llama 3.3 70B, JSON mode) with a closed list of supported intents — the model only returns *which* intent + parameters as JSON, never SQL. The backend then runs the matching, already-parameterized query. The LLM stays on the classification side of the trust boundary, never the execution side.
3. Without an API key, unmatched queries get a helpful "try asking like this" response instead of failing silently.

## Deployment Notes

**Backend (Railway/Render):**
1. Provision a Postgres instance; copy its connection string into `DATABASE_URL`.
2. Deploy `backend/` (Dockerfile included) or point a Python buildpack at it with start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
3. Run `python -m app.seed` once against the deployed database (via a one-off job/shell) to populate it.
4. Set `FRONTEND_ORIGINS` to your deployed frontend URL once you have it, so CORS doesn't block the browser.

**Frontend (Vercel/Netlify):**
1. Point it at `frontend/` as the project root.
2. For local dev, leave `NEXT_PUBLIC_API_URL` unset so the frontend uses the same-origin `/api/*` proxy. For deployment, set `NEXT_PUBLIC_API_URL` only if the browser should call a public backend directly.
3. Default build command (`npm run build`) works as-is.

## Debugging Notes

Issues found and fixed while validating this build against a running instance (see `AI_PROMPTS.md` for the full trail):
- **Case-sensitive lookups in the AI assistant** — both the "seat code" and "employee code" intents did exact-match (`==`) comparisons against values the regex parser had uppercased/lowercased, so `"ETH1001"` typed by a user didn't reliably match the stored `"ETH1001"`. Fixed by switching both to case-insensitive (`ilike`) lookups.
- **Missing rule-based trigger for department headcount** — the intent existed in the executor but had no regex path to reach it, so it silently fell through to "unknown" without an Anthropic API key. Added the missing pattern.
- **Stray directory from a broken brace-expansion** during scaffolding (a literal folder named `{employees/[id],projects,...}`) — removed; had no effect on the app, just repo hygiene.
- Full backend test pass: all CRUD + business-rule endpoints (double-booking, >100% allocation, duplicate email, offboarding cascade, double-release) hit live against a running server — see `AI_PROMPTS.md` for the exact commands and results.
- **Windows + Python 3.14 wheel gaps**: two pinned dependencies (`psycopg2-binary==2.9.9` and `pydantic==2.9.2`, which pulls in `pydantic-core==2.23.4`) predate Python 3.14 and have no prebuilt Windows wheels for it, so `pip` fell back to compiling from source — `psycopg2` needs PostgreSQL's `pg_config`, and `pydantic-core` needs a Rust toolchain + MSVC linker, neither of which are typically present on a fresh machine. Fixed by bumping `psycopg2-binary` to `2.9.12` and `pydantic`/`pydantic-settings` to version ranges (`>=2.12`, where Python 3.14 wheel support was added) that resolve to versions with prebuilt wheels. Re-verified the full CRUD + business-rule + AI-assistant test pass after the bump to confirm nothing broke.
- Frontend: `tsc --noEmit` clean, and a full `next build` completed with zero errors (temporarily swapped the Google Fonts import for the build test only, since this sandbox has no internet access to fonts.googleapis.com — not an issue on a real deploy host).

## Known Limitations / Next Steps

- No authentication/authorization layer — every endpoint is open. A real deployment needs role-based access (Employee/HR/Admin/Project team, per the brief) before going anywhere near real data.
- No Alembic migration history is included — schema currently comes from `Base.metadata.create_all()`. Fine for this assessment; a real system should use versioned migrations.
- Seat map is a list/grid view, not a literal floor-plan visualization.
- Screenshots aren't included in this submission since the app hasn't been deployed to a live URL yet — see `AI_PROMPTS.md` for why they couldn't be generated in the build environment either. Run `npm run dev` + `uvicorn ... --reload` locally (or deploy) and capture them for the final submission.
