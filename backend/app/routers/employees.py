import datetime as dt
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/employees", tags=["Employees"])


def _next_employee_code(db: Session) -> str:
    count = db.query(models.Employee).count()
    return f"ETH{count + 1001}"


@router.get("", response_model=dict)
def list_employees(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    search: str | None = Query(None, description="Search by name, email, or employee code"),
    department_id: int | None = None,
    employment_status: schemas.EmploymentStatus | None = None,
    has_seat: bool | None = Query(None, description="Filter employees who do/don't have an active seat"),
    project_id: int | None = None,
):
    q = db.query(models.Employee).options(joinedload(models.Employee.department))

    if search:
        like = f"%{search}%"
        q = q.filter(or_(
            models.Employee.full_name.ilike(like),
            models.Employee.email.ilike(like),
            models.Employee.employee_code.ilike(like),
        ))
    if department_id:
        q = q.filter(models.Employee.department_id == department_id)
    if employment_status:
        q = q.filter(models.Employee.employment_status == employment_status)
    if project_id:
        q = q.join(models.ProjectAssignment).filter(
            models.ProjectAssignment.project_id == project_id,
            models.ProjectAssignment.is_active == True,  # noqa: E712
        )
    if has_seat is not None:
        seated_ids = db.query(models.SeatAllocation.employee_id).filter(
            models.SeatAllocation.status == models.AllocationStatus.active
        )
        if has_seat:
            q = q.filter(models.Employee.id.in_(seated_ids))
        else:
            q = q.filter(~models.Employee.id.in_(seated_ids))

    total = q.count()
    items = q.order_by(models.Employee.id).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [schemas.EmployeeOut.model_validate(e) for e in items],
    }


@router.get("/{employee_id}", response_model=schemas.EmployeeDetailOut)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    emp = db.query(models.Employee).options(joinedload(models.Employee.department)).get(employee_id)
    if not emp:
        raise HTTPException(404, "Employee not found")

    seat_alloc = db.query(models.SeatAllocation).filter(
        models.SeatAllocation.employee_id == employee_id,
        models.SeatAllocation.status == models.AllocationStatus.active,
    ).first()

    active_assignments = db.query(models.ProjectAssignment).options(
        joinedload(models.ProjectAssignment.project)
    ).filter(
        models.ProjectAssignment.employee_id == employee_id,
        models.ProjectAssignment.is_active == True,  # noqa: E712
    ).all()

    out = schemas.EmployeeDetailOut.model_validate(emp)
    out.current_seat = schemas.SeatOut.model_validate(seat_alloc.seat) if seat_alloc else None
    out.active_projects = [schemas.ProjectAssignmentOut.model_validate(a) for a in active_assignments]
    return out


@router.post("", response_model=schemas.EmployeeOut, status_code=201)
def create_employee(payload: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    if db.query(models.Employee).filter(models.Employee.email == payload.email).first():
        raise HTTPException(400, "An employee with this email already exists")

    data = payload.model_dump()
    data["employee_code"] = data.get("employee_code") or _next_employee_code(db)
    emp = models.Employee(**data)
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


@router.put("/{employee_id}", response_model=schemas.EmployeeOut)
def update_employee(employee_id: int, payload: schemas.EmployeeUpdate, db: Session = Depends(get_db)):
    emp = db.query(models.Employee).get(employee_id)
    if not emp:
        raise HTTPException(404, "Employee not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(emp, k, v)
    emp.updated_at = dt.datetime.utcnow()
    db.commit()
    db.refresh(emp)
    return emp


@router.delete("/{employee_id}", status_code=204)
def offboard_employee(employee_id: int, db: Session = Depends(get_db)):
    """Soft-delete: marks employee as exited and releases their active seat."""
    emp = db.query(models.Employee).get(employee_id)
    if not emp:
        raise HTTPException(404, "Employee not found")

    emp.employment_status = models.EmploymentStatus.exited

    active_seat = db.query(models.SeatAllocation).filter(
        models.SeatAllocation.employee_id == employee_id,
        models.SeatAllocation.status == models.AllocationStatus.active,
    ).first()
    if active_seat:
        active_seat.status = models.AllocationStatus.released
        active_seat.released_date = dt.date.today()

    for a in db.query(models.ProjectAssignment).filter(
        models.ProjectAssignment.employee_id == employee_id,
        models.ProjectAssignment.is_active == True,  # noqa: E712
    ):
        a.is_active = False
        a.end_date = a.end_date or dt.date.today()

    db.commit()
    return None
