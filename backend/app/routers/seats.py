import datetime as dt
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/seats", tags=["Seats"])


@router.get("", response_model=dict)
def list_seats(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    floor_id: int | None = None,
    zone: str | None = None,
    seat_type: schemas.SeatType | None = None,
    occupied: bool | None = Query(None, description="Filter by occupancy"),
):
    q = db.query(models.Seat).options(joinedload(models.Seat.floor)).filter(models.Seat.is_active == True)  # noqa: E712
    if floor_id:
        q = q.filter(models.Seat.floor_id == floor_id)
    if zone:
        q = q.filter(models.Seat.zone == zone)
    if seat_type:
        q = q.filter(models.Seat.seat_type == seat_type)

    # Filter occupancy at the SQL level (not after pagination) so `total`
    # and the returned page are consistent for large datasets.
    if occupied is not None:
        occupied_seat_ids = db.query(models.SeatAllocation.seat_id).filter(
            models.SeatAllocation.status == models.AllocationStatus.active
        )
        q = q.filter(models.Seat.id.in_(occupied_seat_ids)) if occupied else q.filter(~models.Seat.id.in_(occupied_seat_ids))

    total = q.count()
    seats = q.order_by(models.Seat.seat_code).offset((page - 1) * page_size).limit(page_size).all()

    seat_ids_on_page = [s.id for s in seats]
    active_allocs = {
        a.seat_id: a for a in db.query(models.SeatAllocation).options(joinedload(models.SeatAllocation.employee)).filter(
            models.SeatAllocation.status == models.AllocationStatus.active,
            models.SeatAllocation.seat_id.in_(seat_ids_on_page),
        ).all()
    }

    results = []
    for s in seats:
        alloc = active_allocs.get(s.id)
        results.append(schemas.SeatWithStatusOut(
            **schemas.SeatOut.model_validate(s).model_dump(),
            is_occupied=alloc is not None,
            occupant_name=alloc.employee.full_name if alloc else None,
            occupant_id=alloc.employee_id if alloc else None,
        ))

    return {"total": total, "page": page, "page_size": page_size, "items": results}


@router.get("/available", response_model=list[schemas.SeatOut])
def list_available_seats(
    db: Session = Depends(get_db),
    floor_id: int | None = None,
    zone: str | None = None,
    limit: int = Query(50, le=500),
):
    occupied_seat_ids = db.query(models.SeatAllocation.seat_id).filter(
        models.SeatAllocation.status == models.AllocationStatus.active
    )
    q = db.query(models.Seat).filter(
        models.Seat.is_active == True,  # noqa: E712
        ~models.Seat.id.in_(occupied_seat_ids),
    )
    if floor_id:
        q = q.filter(models.Seat.floor_id == floor_id)
    if zone:
        q = q.filter(models.Seat.zone == zone)
    return q.order_by(models.Seat.seat_code).limit(limit).all()


@router.post("/allocate", response_model=schemas.SeatAllocationOut, status_code=201)
def allocate_seat(payload: schemas.SeatAllocationCreate, db: Session = Depends(get_db)):
    seat = db.query(models.Seat).get(payload.seat_id)
    if not seat or not seat.is_active:
        raise HTTPException(404, "Seat not found or inactive")
    emp = db.query(models.Employee).get(payload.employee_id)
    if not emp:
        raise HTTPException(404, "Employee not found")

    # Rule: seat must be free
    seat_taken = db.query(models.SeatAllocation).filter(
        models.SeatAllocation.seat_id == payload.seat_id,
        models.SeatAllocation.status == models.AllocationStatus.active,
    ).first()
    if seat_taken:
        raise HTTPException(400, f"Seat {seat.seat_code} is already occupied")

    # Rule: employee can only hold one active seat
    existing = db.query(models.SeatAllocation).filter(
        models.SeatAllocation.employee_id == payload.employee_id,
        models.SeatAllocation.status == models.AllocationStatus.active,
    ).first()
    if existing:
        raise HTTPException(400, "Employee already has an active seat. Release it before allocating a new one.")

    alloc = models.SeatAllocation(
        seat_id=payload.seat_id,
        employee_id=payload.employee_id,
        allocated_date=dt.date.today(),
        status=models.AllocationStatus.active,
        allocated_by=payload.allocated_by or "system",
        notes=payload.notes,
    )
    db.add(alloc)
    db.commit()
    db.refresh(alloc)
    return alloc


@router.post("/{seat_id}/release", response_model=schemas.SeatAllocationOut)
def release_seat(seat_id: int, payload: schemas.SeatReleaseRequest, db: Session = Depends(get_db)):
    alloc = db.query(models.SeatAllocation).filter(
        models.SeatAllocation.seat_id == seat_id,
        models.SeatAllocation.status == models.AllocationStatus.active,
    ).first()
    if not alloc:
        raise HTTPException(404, "No active allocation found for this seat")

    alloc.status = models.AllocationStatus.released
    alloc.released_date = dt.date.today()
    if payload.notes:
        alloc.notes = payload.notes
    db.commit()
    db.refresh(alloc)
    return alloc


@router.get("/floors", response_model=list[schemas.FloorOut])
def list_floors(db: Session = Depends(get_db)):
    return db.query(models.Floor).order_by(models.Floor.name).all()


@router.get("/history/{employee_id}", response_model=list[schemas.SeatAllocationOut])
def seat_history(employee_id: int, db: Session = Depends(get_db)):
    return db.query(models.SeatAllocation).options(joinedload(models.SeatAllocation.seat)).filter(
        models.SeatAllocation.employee_id == employee_id
    ).order_by(models.SeatAllocation.allocated_date.desc()).all()
