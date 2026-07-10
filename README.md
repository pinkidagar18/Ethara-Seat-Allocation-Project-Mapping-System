# Ethara Seat Allocation & Project Mapping System

A full-stack internal workforce operations platform for managing employee seating, project assignments, new joiner allocation, search, analytics, and AI-assisted natural-language queries for a 5,000-employee organization.

Built with **Next.js**, **FastAPI**, **PostgreSQL**, **SQLAlchemy**, **Tailwind CSS**, and **Recharts**.

## Live Demo

| Service | URL |
|---|---|
| Frontend | https://ethara-seat-allocation-project-mapp-xi.vercel.app/ |
| Backend API | https://ethara-seat-allocation-project-mapping-w0km.onrender.com |
| Swagger Docs | https://ethara-seat-allocation-project-mapping-w0km.onrender.com/docs |
| Health Check | https://ethara-seat-allocation-project-mapping-w0km.onrender.com/health |

## Demo Video

[Watch Demo Video on Google Drive](https://drive.google.com/file/d/1nszMJvsMoWRSn1aUJIJ-DBVrSDw1f2zX/view?usp=sharing)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Screenshots](#screenshots)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Local Setup](#local-setup)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Business Rules](#business-rules)
- [AI Assistant Design](#ai-assistant-design)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Known Limitations](#known-limitations)
- [License](#license)

## Overview

Ethara Seat Allocation & Project Mapping System is an internal admin tool designed for HR, facilities, and project operations teams. It solves the everyday problem of tracking where employees sit, which projects they are assigned to, whether seats are available, and how new joiners can be allocated quickly without double-booking resources.

The system includes a seeded production-style dataset with approximately:

| Entity | Volume |
|---|---:|
| Employees | 5,000 |
| Projects | 150 |
| Seats | 5,240 |
| Floors | 5 |
| Project Assignments | 6,000+ |
| Pending New Joiners | 40 |

## Features

### Employee Management

- Create, view, update, and offboard employees.
- Track departments, designations, reporting managers, joining dates, and employment status.
- Soft-delete/offboard flow releases active seat allocations and ends project assignments.

### Seat Allocation

- Allocate and release seats with double-booking prevention.
- Enforce one active seat per employee.
- Track full seat allocation history.
- Filter seats by floor, zone, type, active status, and occupancy.

### Project Mapping

- Create and manage projects.
- Assign employees to project teams with role and allocation percentage.
- Prevent employees from exceeding 100% allocation across active projects.
- View project team rosters and project headcount.

### New Joiner Allocation

- Create new joiner requests.
- Auto-allocate seats using priority order:
  1. Preferred floor and zone
  2. Preferred floor
  3. Any available seat
  4. Pending queue if no seat is available
- Retry pending allocation later.

### Dashboard & Analytics

- Total employees and active employees.
- Seat utilization and availability.
- Active projects and pending joiner count.
- Utilization by floor.
- Headcount by department and project.

### Search

- Global search across employees, seats, and projects.
- Entity-level filters for faster operations.

### AI Assistant

- Ask natural-language questions like:
  - How many seats are available on Floor 3?
  - Who sits at seat F2-C-012?
  - What is the headcount in Engineering?
  - Which seat is assigned to ETH1001?
- Uses a rule-based intent parser first.
- Optional Groq fallback for supported intent classification.

## Screenshots

### Dashboard

![Dashboard](./Images/Dashboard.png)

### Employees

![Employees](./Images/Employees.png)

### Projects

![Projects](./Images/Projects.png)

### Seat Map

![Seat Map](./Images/Seat_Map.png)

### New Joiner Allocation

![New Joiner](./Images/New_Joinee.png)

### Ask Ethara AI Assistant

![Ask Ethara](./Images/Ask_Ethara.png)

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 App Router, TypeScript, Tailwind CSS |
| Charts | Recharts |
| UI Icons | Lucide React |
| Backend | FastAPI, Python 3.12 |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.0 |
| Validation | Pydantic |
| AI Assistant | Rule-based parser plus optional Groq Llama 3.3 70B |
| Backend Hosting | Render |
| Frontend Hosting | Vercel |

## Project Structure

```text
ethara/
|-- backend/
|   |-- app/
|   |   |-- main.py
|   |   |-- database.py
|   |   |-- models.py
|   |   |-- schemas.py
|   |   |-- seed.py
|   |   `-- routers/
|   |       |-- employees.py
|   |       |-- projects.py
|   |       |-- seats.py
|   |       |-- new_joiners.py
|   |       |-- dashboard.py
|   |       |-- search.py
|   |       `-- assistant.py
|   |-- Dockerfile
|   |-- requirements.txt
|   `-- .env.example
|-- frontend/
|   |-- app/
|   |-- components/
|   |-- lib/
|   |-- public/
|   |-- package.json
|   |-- vercel.json
|   `-- .env.local.example
|-- Images/
|   |-- Dashboard.png
|   |-- Employees.png
|   |-- Projects.png
|   |-- Seat_Map.png
|   |-- New_Joinee.png
|   |-- Ask_Ethara.png
|-- database_schema.sql
|-- docker-compose.yml
|-- render.yaml
|-- start-dev.ps1
`-- README.md
```

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL or Docker
- Git

### Quick Start on Windows

```powershell
.\start-dev.ps1
```

This starts:

| Service | Local URL |
|---|---|
| Backend | http://127.0.0.1:8020 |
| Frontend | http://localhost:3000 |
| Swagger Docs | http://127.0.0.1:8020/docs |

### Manual Backend Setup

```bash
docker compose up -d postgres

cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
python -m app.seed
uvicorn app.main:app --reload --port 8020
```

### Manual Frontend Setup

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

## Environment Variables

### Backend

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection string. |
| `FRONTEND_ORIGINS` | Yes in production | Comma-separated CORS allowlist. |
| `GROQ_API_KEY` | No | Enables optional Groq fallback for AI assistant. |
| `GROQ_MODEL` | No | Defaults to `llama-3.3-70b-versatile`. |
| `ENVIRONMENT` | No | `development` or `production`. |

Example:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/ethara_db
FRONTEND_ORIGINS=http://localhost:3000
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile
ENVIRONMENT=development
```

### Frontend

| Variable | Required | Description |
|---|---|---|
| `API_URL` | Yes | Backend URL used by the Next.js `/api/*` proxy. |
| `NEXT_PUBLIC_API_URL` | No | Optional browser-direct API URL. Usually leave unset. |

Example:

```env
API_URL=http://127.0.0.1:8020
```

## API Endpoints

| Prefix | Purpose |
|---|---|
| `/` | API root |
| `/health` | Health check |
| `/api/employees` | Employee CRUD and offboarding |
| `/api/projects` | Project CRUD and project team management |
| `/api/projects/assignments` | Project assignment management |
| `/api/seats` | Seat listing, allocation, release, and history |
| `/api/new-joiners` | New joiner request and retry allocation |
| `/api/dashboard` | Summary and analytics endpoints |
| `/api/search` | Global search |
| `/api/assistant/query` | Natural-language assistant query |

Open Swagger UI here:

```text
https://ethara-seat-allocation-project-mapping-w0km.onrender.com/docs
```

## Business Rules

1. An employee can have only one active seat at a time.
2. A seat can be actively allocated to only one employee.
3. Project allocation across active projects cannot exceed 100% for one employee.
4. New joiner auto-allocation tries preferred floor and zone first.
5. If no seat is available, the new joiner remains pending.
6. Offboarding is a soft-delete and preserves history.
7. Offboarding releases the active seat and ends active project assignments.
8. Seat allocation history is retained for auditability.

## AI Assistant Design

The assistant avoids allowing an LLM to generate raw SQL. This keeps database access controlled and reduces injection/data exposure risk.

Flow:

1. A local regex/rule parser detects supported intents.
2. The backend executes safe, parameterized ORM queries.
3. If the query does not match a rule and `GROQ_API_KEY` is configured, Groq classifies the intent from a closed list.
4. The LLM never executes SQL and never receives permission to create arbitrary database queries.

Supported examples:

```text
How many available seats are on Floor 3?
Who sits at seat F2-C-012?
What is ETH1001's current seat?
How many employees are in Engineering?
How many pending new joiners are there?
```

## Deployment

### Backend on Render

Use the same GitHub repository and deploy only the backend folder.

Render settings:

```text
Runtime: Docker
Branch: main
Root Directory: backend
Dockerfile Path: ./Dockerfile
```

Required Render environment variables:

```env
DATABASE_URL=<Render PostgreSQL Internal Database URL>
FRONTEND_ORIGINS=https://ethara-seat-allocation-project-mapp-xi.vercel.app
ENVIRONMENT=production
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_API_KEY=<optional>
```

Backend URL:

```text
https://ethara-seat-allocation-project-mapping-w0km.onrender.com
```

### Database Seeding on Render Free Plan

Render Shell is not available on free services. To seed from your local machine, copy the Render PostgreSQL **External Database URL** and run:

```powershell
cd C:\Users\pc\Downloads\ethara-seat-allocation\ethara\backend
$env:DATABASE_URL="PASTE_EXTERNAL_DATABASE_URL_HERE"
.\venv\Scripts\python.exe -m app.seed
```

Important: run the seed command only once for production/demo data. It drops and recreates all tables.

### Frontend on Vercel

Vercel settings:

```text
Framework: Next.js
Root Directory: frontend
Install Command: npm ci
Build Command: npm run build
```

Vercel environment variable:

```env
API_URL=https://ethara-seat-allocation-project-mapping-w0km.onrender.com
```

Frontend URL:

```text
https://ethara-seat-allocation-project-mapp-xi.vercel.app/
```

## Troubleshooting

### Backend connects to localhost on Render

Problem:

```text
connection to server at "localhost", port 5432 failed
```

Cause: `DATABASE_URL` is still using the local development value.

Fix: Replace it with the Render PostgreSQL **Internal Database URL** in the backend web service environment variables.

### Render Docker path error

Problem:

```text
lstat /opt/render/project/src/backend/backend: no such file or directory
```

Cause: `Root Directory` was set to `backend` and `Dockerfile Path` was set to `backend/Dockerfile`, creating a doubled path.

Fix:

```text
Root Directory: backend
Dockerfile Path: ./Dockerfile
```

### CORS errors from Vercel frontend

Cause: Render backend does not allow the deployed Vercel origin.

Fix:

```env
FRONTEND_ORIGINS=https://ethara-seat-allocation-project-mapp-xi.vercel.app
```

Then redeploy the backend.

### Empty dashboard after deployment

Cause: Database has not been seeded.

Fix: Run `python -m app.seed` once against the Render PostgreSQL database.

## Known Limitations

- No authentication or role-based authorization yet.
- No Alembic migration history is included.
- Free Render PostgreSQL expires after the free trial window unless upgraded.
- Render free web services may sleep after inactivity.
- Seat map is a structured list/grid rather than a true floor-plan drawing.

## Future Improvements

- Role-based access for Admin, HR, Manager, and Facilities teams.
- Alembic migrations for production schema changes.
- Visual floor-plan editor for seats.
- CSV import/export for employees and seats.
- Audit dashboard for allocation changes.
- Email notifications for new joiner allocation.
- Advanced assistant intents and reporting queries.

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.

## Author

Built by **Pinki Dagar** for the Ethara technical assessment.
