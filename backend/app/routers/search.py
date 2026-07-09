from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/search", tags=["Search"])


@router.get("", response_model=dict)
def global_search(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """
    One search box that looks across employees, seats, and projects at once —
    used by the top navbar search in the frontend.
    """
    like = f"%{q}%"

    employees = db.query(models.Employee).filter(
        models.Employee.full_name.ilike(like) |
        models.Employee.email.ilike(like) |
        models.Employee.employee_code.ilike(like)
    ).limit(10).all()

    seats = db.query(models.Seat).filter(models.Seat.seat_code.ilike(like)).limit(10).all()

    projects = db.query(models.Project).filter(
        models.Project.name.ilike(like) | models.Project.project_code.ilike(like)
    ).limit(10).all()

    return {
        "employees": [schemas.EmployeeOut.model_validate(e) for e in employees],
        "seats": [schemas.SeatOut.model_validate(s) for s in seats],
        "projects": [schemas.ProjectOut.model_validate(p) for p in projects],
    }
