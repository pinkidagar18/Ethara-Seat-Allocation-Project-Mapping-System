import axios from "axios";

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

export const api = axios.create({ baseURL: API_URL });

// ---------- Types ----------
export interface Department {
  id: number;
  name: string;
  code: string;
}

export interface Employee {
  id: number;
  employee_code: string;
  full_name: string;
  email: string;
  phone?: string;
  designation?: string;
  department_id?: number;
  department?: Department;
  date_of_joining: string;
  employment_status: "active" | "exited";
  reporting_manager_id?: number;
}

export interface Project {
  id: number;
  project_code: string;
  name: string;
  client_name?: string;
  status: "active" | "completed" | "on_hold";
  start_date?: string;
  end_date?: string;
  project_manager_id?: number;
}

export interface ProjectAssignment {
  id: number;
  employee_id: number;
  project_id: number;
  role_on_project?: string;
  allocation_percentage: number;
  start_date: string;
  end_date?: string;
  is_active: boolean;
  project?: Project;
  employee?: Employee;
}

export interface Floor {
  id: number;
  building: string;
  name: string;
}

export interface Seat {
  id: number;
  seat_code: string;
  floor_id: number;
  zone: string;
  seat_type: "regular" | "hot_desk" | "cabin";
  is_active: boolean;
  floor?: Floor;
}

export interface SeatWithStatus extends Seat {
  is_occupied: boolean;
  occupant_name?: string;
  occupant_id?: number;
}

export interface NewJoinerRequest {
  id: number;
  employee_id: number;
  requested_date: string;
  preferred_floor_id?: number;
  preferred_zone?: string;
  status: "pending" | "allocated";
  allocated_seat_id?: number;
  allocated_date?: string;
  employee?: Employee;
  allocated_seat?: Seat;
}

export interface DashboardSummary {
  total_employees: number;
  active_employees: number;
  total_seats: number;
  occupied_seats: number;
  available_seats: number;
  utilization_percentage: number;
  total_projects: number;
  active_projects: number;
  pending_new_joiners: number;
}

export interface FloorUtilization {
  floor_id: number;
  floor_name: string;
  total_seats: number;
  occupied_seats: number;
  utilization_percentage: number;
}

export interface Paginated<T> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
}
