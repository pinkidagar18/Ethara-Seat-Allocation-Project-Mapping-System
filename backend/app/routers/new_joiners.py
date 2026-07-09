import datetime as dt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db
from ..routers.employees import _next_employee_code

router = APIRouter(prefix="/api/new-joiners", tags=["New Joiners"])


def _auto_allocate_seat(db: Session, employee_id: int, preferred_floor_id: int | None, preferred_zone: str | None) -> models.Seat | None:
    """
    Allocation strategy (documented assumption, no spec was supplied for this):
    1. Try an available seat matching BOTH preferred floor and zone.
    2. Fall back to matching floor only.
    3. Fall back to ANY available active seat.
    4. If nothing is free, return None -> request stays 'pending'.
    """
    occupied_ids = db.query(models.SeatAllocation.seat_id).filter(
        models.SeatAllocation.status == models.AllocationStatus.active
    )
    base_q = db.query(models.Seat).filter(
        models.Seat.is_active == True,  # noqa: E712
        ~models.Seat.id.in_(occupied_ids),
    )

    if preferred_floor_id and preferred_zone:
        seat = base_q.filter(
            models.Seat.floor_id == preferred_floor_id,
            models.Seat.zone == preferred_zone,
        ).order_by(models.Seat.seat_code).first()
        if seat:
            return seat

    if preferred_floor_id:
        seat = base_q.filter(models.Seat.floor_id == preferred_floor_id).order_by(models.Seat.seat_code).first()
        if seat:
            return seat

    return base_q.order_by(models.Seat.seat_code).first()


@router.post("", response_model=schemas.NewJoinerOut, status_code=201)
def create_new_joiner(payload: schemas.NewJoinerCreate, db: Session = Depends(get_db)):
    """Creates the employee record AND attempts immediate seat auto-allocation."""
    if db.query(models.Employee).filter(models.Employee.email == payload.employee.email).first():
        raise HTTPException(400, "An employee with this email already exists")

    emp_data = payload.employee.model_dump()
    emp_data["employee_code"] = emp_data.get("employee_code") or _next_employee_code(db)
    emp = models.Employee(**emp_data)
    db.add(emp)
    db.flush()  # get emp.id without committing

    request = models.NewJoinerRequest(
        employee_id=emp.id,
        requested_date=dt.date.today(),
        preferred_floor_id=payload.preferred_floor_id,
        preferred_zone=payload.preferred_zone,
        status=models.JoinerStatus.pending,
    )
    db.add(request)
    db.flush()

    seat = _auto_allocate_seat(db, emp.id, payload.preferred_floor_id, payload.preferred_zone)
    if seat:
        alloc = models.SeatAllocation(
            seat_id=seat.id,
            employee_id=emp.id,
            allocated_date=dt.date.today(),
            status=models.AllocationStatus.active,
            allocated_by="auto-allocation",
        )
        db.add(alloc)
        request.status = models.JoinerStatus.allocated
        request.allocated_seat_id = seat.id
        request.allocated_date = dt.date.today()

    db.commit()
    db.refresh(request)
    return request


@router.get("", response_model=list[schemas.NewJoinerOut])
def list_new_joiners(status: schemas.JoinerStatus | None = None, db: Session = Depends(get_db)):
    q = db.query(models.NewJoinerRequest).options(
        joinedload(models.NewJoinerRequest.employee),
        joinedload(models.NewJoinerRequest.allocated_seat),
    )
    if status:
        q = q.filter(models.NewJoinerRequest.status == status)
    return q.order_by(models.NewJoinerRequest.requested_date.desc()).all()


@router.post("/{request_id}/retry-allocation", response_model=schemas.NewJoinerOut)
def retry_allocation(request_id: int, db: Session = Depends(get_db)):
    """Retries auto-allocation for a joiner that's still pending (e.g. after seats freed up)."""
    request = db.query(models.NewJoinerRequest).get(request_id)
    if not request:
        raise HTTPException(404, "Request not found")
    if request.status == models.JoinerStatus.allocated:
        raise HTTPException(400, "This joiner already has a seat allocated")

    seat = _auto_allocate_seat(db, request.employee_id, request.preferred_floor_id, request.preferred_zone)
    if not seat:
        raise HTTPException(409, "No available seats match the criteria right now")

    alloc = models.SeatAllocation(
        seat_id=seat.id,
        employee_id=request.employee_id,
        allocated_date=dt.date.today(),
        status=models.AllocationStatus.active,
        allocated_by="auto-allocation",
    )
    db.add(alloc)
    request.status = models.JoinerStatus.allocated
    request.allocated_seat_id = seat.id
    request.allocated_date = dt.date.today()
    db.commit()
    db.refresh(request)
    return request
