"""
Seed data generator.

Run with:  python -m app.seed
Env var SEED_EMPLOYEE_COUNT controls volume (default 5000).

Generates: departments, employees, projects, project_assignments,
floors, seats, seat_allocations, and a handful of pending new-joiner
requests (deliberately left unseated so the New Joiner Allocation
screen / retry-allocation endpoint has something to demo).
"""
import os
import random
import datetime as dt
from faker import Faker

from .database import SessionLocal, engine, Base
from . import models

fake = Faker()
Faker.seed(42)
random.seed(42)

EMP_COUNT = int(os.getenv("SEED_EMPLOYEE_COUNT", "5000"))

DEPARTMENTS = [
    ("Engineering", "ENG"), ("Sales", "SAL"), ("Human Resources", "HR"),
    ("Finance", "FIN"), ("Marketing", "MKT"), ("Operations", "OPS"),
    ("Design", "DES"), ("Product", "PRD"), ("Customer Support", "SUP"),
    ("Legal", "LEG"),
]

DESIGNATIONS = [
    "Software Engineer", "Senior Software Engineer", "QA Engineer", "DevOps Engineer",
    "Product Manager", "Business Analyst", "UI/UX Designer", "HR Executive",
    "Finance Analyst", "Marketing Specialist", "Operations Manager", "Sales Executive",
    "Team Lead", "Associate Consultant", "Technical Architect", "Customer Support Executive",
]

FLOORS = ["Floor 1", "Floor 2", "Floor 3", "Floor 4", "Floor 5"]
ZONES = ["Zone A", "Zone B", "Zone C", "Zone D"]
SEATS_PER_ZONE = 65  # 5 floors * 4 zones * 65 = 1300... scaled up below


def reset_db():
    print("Dropping and recreating all tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def seed_departments(db):
    depts = [models.Department(name=n, code=c) for n, c in DEPARTMENTS]
    db.add_all(depts)
    db.commit()
    return {d.code: d.id for d in depts}


def seed_floors_and_seats(db, target_seats: int):
    floors = [models.Floor(building="Main Campus", name=f) for f in FLOORS]
    db.add_all(floors)
    db.commit()
    floor_ids = [f.id for f in floors]

    seats = []
    seats_per_floor_zone = max(1, target_seats // (len(floor_ids) * len(ZONES)))
    counter = 1
    for floor_id, floor_name in zip(floor_ids, FLOORS):
        for zone in ZONES:
            for i in range(1, seats_per_zone_count(seats_per_floor_zone) + 1):
                seat_type = random.choices(
                    [models.SeatType.regular, models.SeatType.hot_desk, models.SeatType.cabin],
                    weights=[0.75, 0.15, 0.10],
                )[0]
                seats.append(models.Seat(
                    seat_code=f"{floor_name.replace(' ', '')}-{zone[-1]}-{i:03d}",
                    floor_id=floor_id,
                    zone=zone,
                    seat_type=seat_type,
                    is_active=True,
                ))
                counter += 1
    db.bulk_save_objects(seats)
    db.commit()
    return floor_ids


def seats_per_zone_count(n):
    return n


def seed_employees(db, dept_ids: dict, count: int):
    codes = set()
    employees = []
    for i in range(count):
        dept_code = random.choice(list(dept_ids.keys()))
        status = models.EmploymentStatus.active if random.random() < 0.95 else models.EmploymentStatus.exited
        doj = fake.date_between(start_date="-5y", end_date="today")
        code = f"ETH{1001 + i}"
        codes.add(code)
        employees.append(models.Employee(
            employee_code=code,
            full_name=fake.name(),
            email=f"{code.lower()}@ethara-corp.com",
            phone=fake.phone_number()[:20],
            designation=random.choice(DESIGNATIONS),
            department_id=dept_ids[dept_code],
            date_of_joining=doj,
            employment_status=status,
        ))
    db.bulk_save_objects(employees)
    db.commit()
    return [e for e in db.query(models.Employee.id, models.Employee.employment_status).all()]


def seed_projects(db, count: int = 150):
    projects = []
    for i in range(count):
        status = random.choices(
            [models.ProjectStatus.active, models.ProjectStatus.completed, models.ProjectStatus.on_hold],
            weights=[0.55, 0.35, 0.10],
        )[0]
        start = fake.date_between(start_date="-3y", end_date="-30d")
        end = None
        if status == models.ProjectStatus.completed:
            end = fake.date_between(start_date=start, end_date="today")
        projects.append(models.Project(
            project_code=f"PRJ{101 + i}",
            name=f"{fake.catch_phrase()}",
            client_name=fake.company(),
            status=status,
            start_date=start,
            end_date=end,
        ))
    db.bulk_save_objects(projects)
    db.commit()
    return [p.id for p in db.query(models.Project.id, models.Project.status).filter(
        models.Project.status == models.ProjectStatus.active
    ).all()]


def seed_project_assignments(db, active_employee_ids, active_project_ids):
    assignments = []
    for emp_id in active_employee_ids:
        num_projects = random.choices([1, 2], weights=[0.7, 0.3])[0]
        chosen = random.sample(active_project_ids, k=min(num_projects, len(active_project_ids)))
        remaining_pct = 100.0
        for idx, proj_id in enumerate(chosen):
            pct = remaining_pct if idx == len(chosen) - 1 else random.choice([50.0, 60.0, 100.0 if len(chosen) == 1 else 50.0])
            pct = min(pct, remaining_pct)
            remaining_pct -= pct
            assignments.append(models.ProjectAssignment(
                employee_id=emp_id,
                project_id=proj_id,
                role_on_project=random.choice(["Developer", "Lead", "Contributor", "Reviewer", "Analyst"]),
                allocation_percentage=pct,
                start_date=fake.date_between(start_date="-2y", end_date="-1d"),
                is_active=True,
            ))
            if remaining_pct <= 0:
                break
    db.bulk_save_objects(assignments)
    db.commit()


def seed_seat_allocations(db, active_employee_ids, seat_fill_ratio=0.90):
    seat_ids = [s.id for s in db.query(models.Seat.id).all()]
    random.shuffle(seat_ids)

    num_to_seat = int(len(active_employee_ids) * seat_fill_ratio)
    num_to_seat = min(num_to_seat, len(seat_ids))
    seated_employees = random.sample(active_employee_ids, k=num_to_seat)

    allocations = []
    for emp_id, seat_id in zip(seated_employees, seat_ids):
        allocations.append(models.SeatAllocation(
            seat_id=seat_id,
            employee_id=emp_id,
            allocated_date=fake.date_between(start_date="-2y", end_date="-1d"),
            status=models.AllocationStatus.active,
            allocated_by="seed-script",
        ))
    db.bulk_save_objects(allocations)
    db.commit()

    unseated = [e for e in active_employee_ids if e not in set(seated_employees)]
    return unseated


def seed_pending_new_joiners(db, unseated_employee_ids, floor_ids, sample_size=40):
    sample = random.sample(unseated_employee_ids, k=min(sample_size, len(unseated_employee_ids)))
    requests = []
    for emp_id in sample:
        requests.append(models.NewJoinerRequest(
            employee_id=emp_id,
            requested_date=fake.date_between(start_date="-30d", end_date="today"),
            preferred_floor_id=random.choice(floor_ids) if random.random() < 0.5 else None,
            preferred_zone=random.choice(ZONES) if random.random() < 0.5 else None,
            status=models.JoinerStatus.pending,
        ))
    db.bulk_save_objects(requests)
    db.commit()


def run():
    reset_db()
    db = SessionLocal()
    try:
        print(f"Seeding {EMP_COUNT} employees...")
        dept_ids = seed_departments(db)

        # ~10% more seats than active headcount so there's visible spare capacity
        target_seats = int(EMP_COUNT * 1.05)
        floor_ids = seed_floors_and_seats(db, target_seats)

        seed_employees(db, dept_ids, EMP_COUNT)

        active_employee_ids = [
            e.id for e in db.query(models.Employee.id).filter(
                models.Employee.employment_status == models.EmploymentStatus.active
            ).all()
        ]

        active_project_ids = seed_projects(db, count=150)
        seed_project_assignments(db, active_employee_ids, active_project_ids)

        unseated = seed_seat_allocations(db, active_employee_ids, seat_fill_ratio=0.90)
        seed_pending_new_joiners(db, unseated, floor_ids, sample_size=40)

        print("Seed complete:")
        print(f"  Departments: {db.query(models.Department).count()}")
        print(f"  Employees:   {db.query(models.Employee).count()}")
        print(f"  Projects:    {db.query(models.Project).count()}")
        print(f"  Assignments: {db.query(models.ProjectAssignment).count()}")
        print(f"  Floors:      {db.query(models.Floor).count()}")
        print(f"  Seats:       {db.query(models.Seat).count()}")
        print(f"  Allocations: {db.query(models.SeatAllocation).count()}")
        print(f"  Pending new joiners: {db.query(models.NewJoinerRequest).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
