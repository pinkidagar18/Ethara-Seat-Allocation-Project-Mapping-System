"""
Natural-language query interface.

Design decision (documented in README/AI_PROMPTS.md too):
We do NOT let the LLM generate raw SQL and execute it — that's an injection
risk on a system holding 5,000 employees' PII. Instead:

  1. A lightweight rule-based parser handles the common question shapes
     with zero external dependency / zero API cost.
  2. If GROQ_API_KEY is set, unmatched queries are sent to Groq (Llama 3.3
     70B) with a *closed* menu of supported "intents". The model only ever
     returns which intent + which parameters (JSON) — never SQL — and our
     code runs the matching, already-parameterized query. This keeps the
     LLM on the "classification" side of the trust boundary, not the
     "code execution" side.
"""
import os
import re
import json
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/assistant", tags=["AI Assistant"])
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

SUPPORTED_INTENTS = """
- available_seats_on_floor(floor_name: str)
- utilization_of_floor(floor_name: str)
- headcount_of_project(project_name: str)
- headcount_of_department(department_name: str)
- who_sits_at_seat(seat_code: str)
- current_seat_of_employee(employee_name_or_code: str)
- pending_new_joiners_count()
- total_available_seats()
- employees_without_seat_count()
- floor_with_most_available_seats()
- greeting()
- unknown()
"""


def _rule_based_parse(q: str) -> dict | None:
    ql = q.lower().strip()


    if ql in {"hi", "hello", "hey", "good morning", "good afternoon", "good evening"}:
        return {"intent": "greeting", "params": {}}

    if (("most" in ql or "maximum" in ql or "highest" in ql) and ("available" in ql or "free" in ql) and "floor" in ql):
        return {"intent": "floor_with_most_available_seats", "params": {}}
    m = re.search(r"(?:available|free) seats?.*(?:floor|level)\s*([\w\d]+)", ql)
    if m:
        return {"intent": "available_seats_on_floor", "params": {"floor_name": m.group(1)}}

    m = re.search(r"utili[sz]ation.*(?:floor|level)\s*([\w\d]+)", ql)
    if m:
        return {"intent": "utilization_of_floor", "params": {"floor_name": m.group(1)}}

    m = re.search(r"how many (?:people|employees|members).*project[:\s]+([\w\s]+)", ql)
    if m:
        return {"intent": "headcount_of_project", "params": {"project_name": m.group(1).strip()}}

    m = re.search(r"how many (?:people|employees|members).*department[:\s]+([\w\s]+)", ql)
    if m:
        return {"intent": "headcount_of_department", "params": {"department_name": m.group(1).strip()}}

    m = re.search(r"headcount (?:on|for|of) (?:project\s+)?([\w\s]+)", ql)
    if m:
        return {"intent": "headcount_of_project", "params": {"project_name": m.group(1).strip()}}

    m = re.search(r"who (?:is|sits|sitting) at seat\s*([\w\-]+)", ql)
    if m:
        return {"intent": "who_sits_at_seat", "params": {"seat_code": m.group(1).upper()}}

    m = re.search(r"(?:where does|what seat does|seat of)\s+([\w\s]+?)\s*(?:sit|have|sitting)", ql)
    if m:
        return {"intent": "current_seat_of_employee", "params": {"employee_name_or_code": m.group(1).strip()}}

    if "pending" in ql and "joiner" in ql:
        return {"intent": "pending_new_joiners_count", "params": {}}

    if "how many" in ql and "available" in ql and "seat" in ql:
        return {"intent": "total_available_seats", "params": {}}

    if "without a seat" in ql or "no seat" in ql or "unseated" in ql:
        return {"intent": "employees_without_seat_count", "params": {}}

    return None


def _groq_parse(q: str) -> dict:
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=200,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You classify a facilities/HR question into ONE of a fixed set of intents. "
                    "Respond ONLY with compact JSON: {\"intent\": \"...\", \"params\": {...}}. "
                    f"Supported intents:\n{SUPPORTED_INTENTS}\n"
                    "If nothing matches, return {\"intent\": \"unknown\", \"params\": {}}."
                ),
            },
            {"role": "user", "content": q},
        ],
    )
    text = completion.choices[0].message.content.strip().strip("`")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"intent": "unknown", "params": {}}



def _find_floor(db: Session, floor_name: str | None):
    raw = (floor_name or "").strip()
    if not raw:
        return None

    direct = db.query(models.Floor).filter(models.Floor.name.ilike(f"%{raw}%")).first()
    if direct:
        return direct

    number = re.search(r"\d+", raw)
    if number:
        floor_number = number.group(0)
        return db.query(models.Floor).filter(
            models.Floor.name.ilike(f"%floor {floor_number}%") | models.Floor.name.ilike(f"%{floor_number}%")
        ).first()

    return None


def _available_seats_for_floor(db: Session, floor: models.Floor):
    occupied_ids = db.query(models.SeatAllocation.seat_id).filter(
        models.SeatAllocation.status == models.AllocationStatus.active
    )
    return db.query(models.Seat).filter(
        models.Seat.floor_id == floor.id,
        models.Seat.is_active == True,  # noqa: E712
        ~models.Seat.id.in_(occupied_ids),
    ).all()

def _execute_intent(intent: str, params: dict, db: Session) -> schemas.AssistantResponse:
    if intent == "available_seats_on_floor":
        floor = _find_floor(db, params.get("floor_name", ""))
        if not floor:
            return schemas.AssistantResponse(answer="I couldn't find that floor.", interpreted_as=intent)
        seats = _available_seats_for_floor(db, floor)
        return schemas.AssistantResponse(
            answer=f"There are {len(seats)} available seat(s) on {floor.name}.",
            data=[s.seat_code for s in seats[:25]],
            interpreted_as=intent,
        )

    if intent == "utilization_of_floor":
        floor = _find_floor(db, params.get("floor_name", ""))
        if not floor:
            return schemas.AssistantResponse(answer="I couldn't find that floor.", interpreted_as=intent)
        total = db.query(models.Seat).filter(models.Seat.floor_id == floor.id, models.Seat.is_active == True).count()  # noqa: E712
        occupied = db.query(models.SeatAllocation).join(models.Seat).filter(
            models.Seat.floor_id == floor.id, models.SeatAllocation.status == models.AllocationStatus.active
        ).count()
        pct = round((occupied / total) * 100, 1) if total else 0
        return schemas.AssistantResponse(answer=f"{floor.name} is at {pct}% utilization ({occupied}/{total} seats occupied).", interpreted_as=intent)

    if intent == "headcount_of_project":
        proj = db.query(models.Project).filter(models.Project.name.ilike(f"%{params.get('project_name','')}%")).first()
        if not proj:
            return schemas.AssistantResponse(answer="I couldn't find that project.", interpreted_as=intent)
        count = db.query(models.ProjectAssignment).filter(
            models.ProjectAssignment.project_id == proj.id, models.ProjectAssignment.is_active == True  # noqa: E712
        ).count()
        return schemas.AssistantResponse(answer=f"{proj.name} currently has {count} active member(s).", interpreted_as=intent)

    if intent == "headcount_of_department":
        dept = db.query(models.Department).filter(models.Department.name.ilike(f"%{params.get('department_name','')}%")).first()
        if not dept:
            return schemas.AssistantResponse(answer="I couldn't find that department.", interpreted_as=intent)
        count = db.query(models.Employee).filter(
            models.Employee.department_id == dept.id, models.Employee.employment_status == models.EmploymentStatus.active
        ).count()
        return schemas.AssistantResponse(answer=f"{dept.name} has {count} active employee(s).", interpreted_as=intent)

    if intent == "who_sits_at_seat":
        seat = db.query(models.Seat).filter(models.Seat.seat_code.ilike(params.get("seat_code", ""))).first()
        if not seat:
            return schemas.AssistantResponse(answer="I couldn't find that seat code.", interpreted_as=intent)
        alloc = db.query(models.SeatAllocation).filter(
            models.SeatAllocation.seat_id == seat.id, models.SeatAllocation.status == models.AllocationStatus.active
        ).first()
        if not alloc:
            return schemas.AssistantResponse(answer=f"Seat {seat.seat_code} is currently unoccupied.", interpreted_as=intent)
        return schemas.AssistantResponse(answer=f"Seat {seat.seat_code} is occupied by {alloc.employee.full_name}.", interpreted_as=intent)

    if intent == "current_seat_of_employee":
        name = params.get("employee_name_or_code", "")
        emp = db.query(models.Employee).filter(
            models.Employee.full_name.ilike(f"%{name}%") | models.Employee.employee_code.ilike(name)
        ).first()
        if not emp:
            return schemas.AssistantResponse(answer="I couldn't find that employee.", interpreted_as=intent)
        alloc = db.query(models.SeatAllocation).filter(
            models.SeatAllocation.employee_id == emp.id, models.SeatAllocation.status == models.AllocationStatus.active
        ).first()
        if not alloc:
            return schemas.AssistantResponse(answer=f"{emp.full_name} doesn't currently have a seat assigned.", interpreted_as=intent)
        return schemas.AssistantResponse(answer=f"{emp.full_name} sits at seat {alloc.seat.seat_code}.", interpreted_as=intent)

    if intent == "pending_new_joiners_count":
        count = db.query(models.NewJoinerRequest).filter(models.NewJoinerRequest.status == models.JoinerStatus.pending).count()
        return schemas.AssistantResponse(answer=f"There are {count} new joiner(s) waiting on seat allocation.", interpreted_as=intent)

    if intent == "total_available_seats":
        total = db.query(models.Seat).filter(models.Seat.is_active == True).count()  # noqa: E712
        occupied = db.query(models.SeatAllocation).filter(models.SeatAllocation.status == models.AllocationStatus.active).count()
        return schemas.AssistantResponse(answer=f"{total - occupied} seat(s) are currently available out of {total} total.", interpreted_as=intent)

    if intent == "floor_with_most_available_seats":
        floors = db.query(models.Floor).all()
        if not floors:
            return schemas.AssistantResponse(answer="I couldn't find any floors.", interpreted_as=intent)
        rows = [(floor, len(_available_seats_for_floor(db, floor))) for floor in floors]
        floor, count = max(rows, key=lambda item: item[1])
        details = [f"{f.name}: {available}" for f, available in sorted(rows, key=lambda item: item[0].name)]
        return schemas.AssistantResponse(
            answer=f"{floor.name} has the most available seats with {count} seat(s) free.",
            data=details,
            interpreted_as=intent,
        )
    if intent == "employees_without_seat_count":
        seated_ids = db.query(models.SeatAllocation.employee_id).filter(models.SeatAllocation.status == models.AllocationStatus.active)
        count = db.query(models.Employee).filter(
            models.Employee.employment_status == models.EmploymentStatus.active, ~models.Employee.id.in_(seated_ids)
        ).count()
        return schemas.AssistantResponse(answer=f"{count} active employee(s) currently have no seat assigned.", interpreted_as=intent)

    if intent == "greeting":
        return schemas.AssistantResponse(
            answer="Hi! Ask me about seat availability, floor utilization, project headcount, pending joiners, or who sits at a seat.",
            interpreted_as=intent,
        )

    return schemas.AssistantResponse(
        answer=(
            "I didn't quite catch that. Try things like: "
            "'How many available seats on Floor 3?', 'Who sits at seat F3-A-014?', "
            "'Headcount on Project Atlas', or 'How many pending new joiners?'"
        ),
        interpreted_as="unknown",
    )


@router.post("/query", response_model=schemas.AssistantResponse)
def ask_assistant(payload: schemas.AssistantQuery, db: Session = Depends(get_db)):
    parsed = _rule_based_parse(payload.query)
    if parsed is None:
        if GROQ_API_KEY:
            try:
                parsed = _groq_parse(payload.query)
            except Exception as exc:
                logger.warning("Groq assistant fallback failed; using unknown intent: %s", exc)
                parsed = {"intent": "unknown", "params": {}}
        else:
            parsed = {"intent": "unknown", "params": {}}
    return _execute_intent(parsed.get("intent", "unknown"), parsed.get("params", {}), db)
