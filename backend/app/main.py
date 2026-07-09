import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from .routers import employees, projects, seats, new_joiners, dashboard, search, assistant

# Creates tables if they don't exist yet. For production schema changes,
# use Alembic migrations (see /alembic) instead of relying on this.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Ethara Seat Allocation & Project Mapping API",
    description="Manages seat allocation and project mapping for ~5,000 employees.",
    version="1.0.0",
)

origins = [o.strip() for o in os.getenv("FRONTEND_ORIGINS", "http://localhost:3000").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(employees.router)
app.include_router(projects.router)
app.include_router(seats.router)
app.include_router(new_joiners.router)
app.include_router(dashboard.router)
app.include_router(search.router)
app.include_router(assistant.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "Ethara Seat Allocation API", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}
