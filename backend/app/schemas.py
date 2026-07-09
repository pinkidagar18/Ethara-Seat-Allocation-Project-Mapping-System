import datetime as dt
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator

from .models import EmploymentStatus, ProjectStatus, SeatType, AllocationStatus, JoinerStatus


# ---------- Department ----------
class DepartmentBase(BaseModel):
    name: str
    code: str


class DepartmentOut(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- Employee ----------
class EmployeeBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    designation: Optional[str] = None
    department_id: Optional[int] = None
    date_of_joining: dt.date
    reporting_manager_id: Optional[int] = None


class EmployeeCreate(EmployeeBase):
    employee_code: Optional[str] = None  # auto-generated if omitted


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    designation: Optional[str] = None
    department_id: Optional[int] = None
    reporting_manager_id: Optional[int] = None
    employment_status: Optional[EmploymentStatus] = None


class EmployeeOut(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_code: str
    employment_status: EmploymentStatus
    department: Optional[DepartmentOut] = None


class EmployeeDetailOut(EmployeeOut):
    current_seat: Optional["SeatOut"] = None
    active_projects: List["ProjectAssignmentOut"] = []


# ---------- Project ----------
class ProjectBase(BaseModel):
    name: str
    client_name: Optional[str] = None
    status: ProjectStatus = ProjectStatus.active
    start_date: Optional[dt.date] = None
    end_date: Optional[dt.date] = None
    project_manager_id: Optional[int] = None


class ProjectCreate(ProjectBase):
    project_code: Optional[str] = None


class ProjectOut(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_code: str


# ---------- Project Assignment ----------
class ProjectAssignmentCreate(BaseModel):
    employee_id: int
    project_id: int
    role_on_project: Optional[str] = None
    allocation_percentage: float = 100.0
    start_date: dt.date
    end_date: Optional[dt.date] = None

    @field_validator("allocation_percentage")
    @classmethod
    def check_pct(cls, v):
        if not (0 < v <= 100):
            raise ValueError("allocation_percentage must be between 0 and 100")
        return v


class ProjectAssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    project_id: int
    role_on_project: Optional[str]
    allocation_percentage: float
    start_date: dt.date
    end_date: Optional[dt.date]
    is_active: bool
    project: Optional[ProjectOut] = None


# ---------- Floor / Seat ----------
class FloorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    building: str
    name: str


class SeatOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    seat_code: str
    floor_id: int
    zone: str
    seat_type: SeatType
    is_active: bool
    floor: Optional[FloorOut] = None


class SeatWithStatusOut(SeatOut):
    is_occupied: bool
    occupant_name: Optional[str] = None
    occupant_id: Optional[int] = None


# ---------- Seat Allocation ----------
class SeatAllocationCreate(BaseModel):
    seat_id: int
    employee_id: int
    allocated_by: Optional[str] = "system"
    notes: Optional[str] = None


class SeatAllocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    seat_id: int
    employee_id: int
    allocated_date: dt.date
    released_date: Optional[dt.date]
    status: AllocationStatus
    allocated_by: str
    seat: Optional[SeatOut] = None
    employee: Optional[EmployeeOut] = None


class SeatReleaseRequest(BaseModel):
    notes: Optional[str] = None


# ---------- New Joiner ----------
class NewJoinerCreate(BaseModel):
    employee: EmployeeCreate
    preferred_floor_id: Optional[int] = None
    preferred_zone: Optional[str] = None


class NewJoinerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    requested_date: dt.date
    preferred_floor_id: Optional[int]
    preferred_zone: Optional[str]
    status: JoinerStatus
    allocated_seat_id: Optional[int]
    allocated_date: Optional[dt.date]
    employee: Optional[EmployeeOut] = None
    allocated_seat: Optional[SeatOut] = None


# ---------- Dashboard ----------
class DashboardSummary(BaseModel):
    total_employees: int
    active_employees: int
    total_seats: int
    occupied_seats: int
    available_seats: int
    utilization_percentage: float
    total_projects: int
    active_projects: int
    pending_new_joiners: int


class FloorUtilization(BaseModel):
    floor_id: int
    floor_name: str
    total_seats: int
    occupied_seats: int
    utilization_percentage: float


class DepartmentHeadcount(BaseModel):
    department: str
    headcount: int


class ProjectHeadcount(BaseModel):
    project: str
    headcount: int


# ---------- AI Assistant ----------
class AssistantQuery(BaseModel):
    query: str


class AssistantResponse(BaseModel):
    answer: str
    data: Optional[list] = None
    interpreted_as: Optional[str] = None


EmployeeDetailOut.model_rebuild()
