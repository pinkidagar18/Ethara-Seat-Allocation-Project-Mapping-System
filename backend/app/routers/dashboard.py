from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=schemas.DashboardSummary)
def summary(db: Session = Depends(get_db)):
    total_employees = db.query(models.Employee).count()
    active_employees = db.query(models.Employee).filter(
        models.Employee.employment_status == models.EmploymentStatus.active
    ).count()
    total_seats = db.query(models.Seat).filter(models.Seat.is_active == True).count()  # noqa: E712
    occupied_seats = db.query(models.SeatAllocation).filter(
        models.SeatAllocation.status == models.AllocationStatus.active
    ).count()
    total_projects = db.query(models.Project).count()
    active_projects = db.query(models.Project).filter(
        models.Project.status == models.ProjectStatus.active
    ).count()
    pending_new_joiners = db.query(models.NewJoinerRequest).filter(
        models.NewJoinerRequest.status == models.JoinerStatus.pending
    ).count()

    utilization = round((occupied_seats / total_seats) * 100, 2) if total_seats else 0.0

    return schemas.DashboardSummary(
        total_employees=total_employees,
        active_employees=active_employees,
        total_seats=total_seats,
        occupied_seats=occupied_seats,
        available_seats=total_seats - occupied_seats,
        utilization_percentage=utilization,
        total_projects=total_projects,
        active_projects=active_projects,
        pending_new_joiners=pending_new_joiners,
    )


@router.get("/utilization-by-floor", response_model=list[schemas.FloorUtilization])
def utilization_by_floor(db: Session = Depends(get_db)):
    floors = db.query(models.Floor).all()
    results = []
    for f in floors:
        total = db.query(models.Seat).filter(models.Seat.floor_id == f.id, models.Seat.is_active == True).count()  # noqa: E712
        occupied = db.query(models.SeatAllocation).join(models.Seat).filter(
            models.Seat.floor_id == f.id,
            models.SeatAllocation.status == models.AllocationStatus.active,
        ).count()
        results.append(schemas.FloorUtilization(
            floor_id=f.id,
            floor_name=f.name,
            total_seats=total,
            occupied_seats=occupied,
            utilization_percentage=round((occupied / total) * 100, 2) if total else 0.0,
        ))
    return results


@router.get("/headcount-by-department", response_model=list[schemas.DepartmentHeadcount])
def headcount_by_department(db: Session = Depends(get_db)):
    rows = db.query(models.Department.name, func.count(models.Employee.id)).join(
        models.Employee, models.Employee.department_id == models.Department.id
    ).filter(
        models.Employee.employment_status == models.EmploymentStatus.active
    ).group_by(models.Department.name).all()
    return [schemas.DepartmentHeadcount(department=name, headcount=count) for name, count in rows]


@router.get("/headcount-by-project", response_model=list[schemas.ProjectHeadcount])
def headcount_by_project(db: Session = Depends(get_db)):
    rows = db.query(models.Project.name, func.count(models.ProjectAssignment.id)).join(
        models.ProjectAssignment, models.ProjectAssignment.project_id == models.Project.id
    ).filter(
        models.ProjectAssignment.is_active == True  # noqa: E712
    ).group_by(models.Project.name).order_by(func.count(models.ProjectAssignment.id).desc()).limit(15).all()
    return [schemas.ProjectHeadcount(project=name, headcount=count) for name, count in rows]
