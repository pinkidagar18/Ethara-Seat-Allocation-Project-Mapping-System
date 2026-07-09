-- Ethara Seat Allocation & Project Mapping System
-- PostgreSQL schema, generated from SQLAlchemy models (backend/app/models.py)
-- Generate/update this file by re-running the export used in AI_PROMPTS.md

CREATE TABLE departments (
	id SERIAL NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	UNIQUE (code)
);

CREATE TABLE floors (
	id SERIAL NOT NULL, 
	building VARCHAR(100), 
	name VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_building_floor UNIQUE (building, name)
);

CREATE TABLE employees (
	id SERIAL NOT NULL, 
	employee_code VARCHAR(20) NOT NULL, 
	full_name VARCHAR(150) NOT NULL, 
	email VARCHAR(150) NOT NULL, 
	phone VARCHAR(20), 
	designation VARCHAR(100), 
	department_id INTEGER, 
	date_of_joining DATE NOT NULL, 
	employment_status employmentstatus NOT NULL, 
	reporting_manager_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(department_id) REFERENCES departments (id), 
	FOREIGN KEY(reporting_manager_id) REFERENCES employees (id)
);

CREATE TABLE seats (
	id SERIAL NOT NULL, 
	seat_code VARCHAR(30) NOT NULL, 
	floor_id INTEGER NOT NULL, 
	zone VARCHAR(20) NOT NULL, 
	seat_type seattype NOT NULL, 
	is_active BOOLEAN, 
	PRIMARY KEY (id), 
	FOREIGN KEY(floor_id) REFERENCES floors (id)
);

CREATE TABLE new_joiner_requests (
	id SERIAL NOT NULL, 
	employee_id INTEGER NOT NULL, 
	requested_date DATE NOT NULL, 
	preferred_floor_id INTEGER, 
	preferred_zone VARCHAR(20), 
	status joinerstatus NOT NULL, 
	allocated_seat_id INTEGER, 
	allocated_date DATE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(employee_id) REFERENCES employees (id), 
	FOREIGN KEY(preferred_floor_id) REFERENCES floors (id), 
	FOREIGN KEY(allocated_seat_id) REFERENCES seats (id)
);

CREATE TABLE projects (
	id SERIAL NOT NULL, 
	project_code VARCHAR(20) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	client_name VARCHAR(150), 
	status projectstatus NOT NULL, 
	start_date DATE, 
	end_date DATE, 
	project_manager_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_manager_id) REFERENCES employees (id)
);

CREATE TABLE seat_allocations (
	id SERIAL NOT NULL, 
	seat_id INTEGER NOT NULL, 
	employee_id INTEGER NOT NULL, 
	allocated_date DATE NOT NULL, 
	released_date DATE, 
	status allocationstatus NOT NULL, 
	allocated_by VARCHAR(100), 
	notes TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(seat_id) REFERENCES seats (id), 
	FOREIGN KEY(employee_id) REFERENCES employees (id)
);

CREATE TABLE project_assignments (
	id SERIAL NOT NULL, 
	employee_id INTEGER NOT NULL, 
	project_id INTEGER NOT NULL, 
	role_on_project VARCHAR(100), 
	allocation_percentage FLOAT NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE, 
	is_active BOOLEAN, 
	PRIMARY KEY (id), 
	FOREIGN KEY(employee_id) REFERENCES employees (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
);
