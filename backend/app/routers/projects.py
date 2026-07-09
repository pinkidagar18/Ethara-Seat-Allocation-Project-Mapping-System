from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/projects", tags=["Projects"])


def _next_project_code(db: Session) -> str:
    count = db.query(models.Project).count()
    return f"PRJ{count + 101}"


@router.get("", response_model=dict)
def list_projects(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    search: str | None = None,
    status: schemas.ProjectStatus | None = None,
):
    q = db.query(models.Project)
    if search:
        like = f"%{search}%"
        q = q.filter(models.Project.name.ilike(like) | models.Project.client_name.ilike(like))
    if status:
        q = q.filter(models.Project.status == status)

    total = q.count()
    items = q.order_by(models.Project.id).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size,
            "items": [schemas.ProjectOut.model_validate(p) for p in items]}


@router.get("/{project_id}", response_model=schemas.ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Project).get(project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    return p


@router.post("", response_model=schemas.ProjectOut, status_code=201)
def create_project(payload: schemas.ProjectCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    data["project_code"] = data.get("project_code") or _next_project_code(db)
    p = models.Project(**data)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("/{project_id}/team", response_model=list[schemas.ProjectAssignmentOut])
def get_project_team(project_id: int, db: Session = Depends(get_db)):
    assignments = db.query(models.ProjectAssignment).options(
        joinedload(models.ProjectAssignment.employee)
    ).filter(
        models.ProjectAssignment.project_id == project_id,
        models.ProjectAssignment.is_active == True,  # noqa: E712
    ).all()
    return assignments


@router.post("/assignments", response_model=schemas.ProjectAssignmentOut, status_code=201)
def assign_employee_to_project(payload: schemas.ProjectAssignmentCreate, db: Session = Depends(get_db)):
    emp = db.query(models.Employee).get(payload.employee_id)
    if not emp:
        raise HTTPException(404, "Employee not found")
    proj = db.query(models.Project).get(payload.project_id)
    if not proj:
        raise HTTPException(404, "Project not found")

    # Business rule: sum of active allocation % across a person's projects cannot exceed 100
    existing_pct = db.query(models.ProjectAssignment).filter(
        models.ProjectAssignment.employee_id == payload.employee_id,
        models.ProjectAssignment.is_active == True,  # noqa: E712
    ).all()
    total_pct = sum(a.allocation_percentage for a in existing_pct) + payload.allocation_percentage
    if total_pct > 100:
        raise HTTPException(400, f"Allocation exceeds 100% (current + new = {total_pct}%)")

    assignment = models.ProjectAssignment(**payload.model_dump())
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.delete("/assignments/{assignment_id}", status_code=204)
def end_assignment(assignment_id: int, db: Session = Depends(get_db)):
    a = db.query(models.ProjectAssignment).get(assignment_id)
    if not a:
        raise HTTPException(404, "Assignment not found")
    a.is_active = False
    import datetime as dt
    a.end_date = a.end_date or dt.date.today()
    db.commit()
    return None
