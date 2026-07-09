import enum
import datetime as dt

from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime, ForeignKey,
    Enum, Float, Text, UniqueConstraint, func
)
from sqlalchemy.orm import relationship

from .database import Base


class EmploymentStatus(str, enum.Enum):
    active = "active"
    exited = "exited"


class ProjectStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    on_hold = "on_hold"


class SeatType(str, enum.Enum):
    regular = "regular"
    hot_desk = "hot_desk"
    cabin = "cabin"


class AllocationStatus(str, enum.Enum):
    active = "active"
    released = "released"


class JoinerStatus(str, enum.Enum):
    pending = "pending"
    allocated = "allocated"


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=False)

    employees = relationship("Employee", back_populates="department")


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True)
    employee_code = Column(String(20), unique=True, nullable=False, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    phone = Column(String(20))
    designation = Column(String(100))
    department_id = Column(Integer, ForeignKey("departments.id"))
    date_of_joining = Column(Date, nullable=False)
    employment_status = Column(Enum(EmploymentStatus), default=EmploymentStatus.active, nullable=False, index=True)
    reporting_manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    department = relationship("Department", back_populates="employees")
    manager = relationship("Employee", remote_side=[id])

    project_assignments = relationship("ProjectAssignment", back_populates="employee", foreign_keys="ProjectAssignment.employee_id")
    seat_allocations = relationship("SeatAllocation", back_populates="employee", foreign_keys="SeatAllocation.employee_id")
    new_joiner_request = relationship("NewJoinerRequest", back_populates="employee", uselist=False, foreign_keys="NewJoinerRequest.employee_id")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    project_code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    client_name = Column(String(150))
    status = Column(Enum(ProjectStatus), default=ProjectStatus.active, nullable=False, index=True)
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    project_manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    project_manager = relationship("Employee", foreign_keys=[project_manager_id])
    assignments = relationship("ProjectAssignment", back_populates="project")


class ProjectAssignment(Base):
    __tablename__ = "project_assignments"

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    role_on_project = Column(String(100))
    allocation_percentage = Column(Float, default=100.0, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, index=True)

    employee = relationship("Employee", back_populates="project_assignments", foreign_keys=[employee_id])
    project = relationship("Project", back_populates="assignments")


class Floor(Base):
    __tablename__ = "floors"

    id = Column(Integer, primary_key=True)
    building = Column(String(100), default="Main Campus")
    name = Column(String(50), nullable=False)  # e.g. "Floor 3"

    seats = relationship("Seat", back_populates="floor")

    __table_args__ = (UniqueConstraint("building", "name", name="uq_building_floor"),)


class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True)
    seat_code = Column(String(30), unique=True, nullable=False, index=True)  # e.g. F3-A-014
    floor_id = Column(Integer, ForeignKey("floors.id"), nullable=False, index=True)
    zone = Column(String(20), nullable=False)  # e.g. Zone A
    seat_type = Column(Enum(SeatType), default=SeatType.regular, nullable=False)
    is_active = Column(Boolean, default=True)  # false = under maintenance / decommissioned

    floor = relationship("Floor", back_populates="seats")
    allocations = relationship("SeatAllocation", back_populates="seat")


class SeatAllocation(Base):
    __tablename__ = "seat_allocations"

    id = Column(Integer, primary_key=True)
    seat_id = Column(Integer, ForeignKey("seats.id"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    allocated_date = Column(Date, nullable=False, default=dt.date.today)
    released_date = Column(Date, nullable=True)
    status = Column(Enum(AllocationStatus), default=AllocationStatus.active, nullable=False, index=True)
    allocated_by = Column(String(100), default="system")
    notes = Column(Text, nullable=True)

    seat = relationship("Seat", back_populates="allocations")
    employee = relationship("Employee", back_populates="seat_allocations", foreign_keys=[employee_id])


class NewJoinerRequest(Base):
    __tablename__ = "new_joiner_requests"

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), unique=True, nullable=False, index=True)
    requested_date = Column(Date, default=dt.date.today, nullable=False)
    preferred_floor_id = Column(Integer, ForeignKey("floors.id"), nullable=True)
    preferred_zone = Column(String(20), nullable=True)
    status = Column(Enum(JoinerStatus), default=JoinerStatus.pending, nullable=False, index=True)
    allocated_seat_id = Column(Integer, ForeignKey("seats.id"), nullable=True)
    allocated_date = Column(Date, nullable=True)

    employee = relationship("Employee", back_populates="new_joiner_request", foreign_keys=[employee_id])
    preferred_floor = relationship("Floor", foreign_keys=[preferred_floor_id])
    allocated_seat = relationship("Seat", foreign_keys=[allocated_seat_id])
