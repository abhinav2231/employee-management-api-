from datetime import date
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.employee import Employee
from app.models.role import Role, EmployeeRole


def test_list_departments_empty(client: TestClient):
    """Ensure empty list is returned when no departments exist."""
    response = client.get("/api/v1/departments")
    assert response.status_code == 200
    assert response.json() == []


def test_list_departments_with_counts(client: TestClient, db: Session):
    """Test department listing calculates active employee counts accurately."""
    dept1 = Department(name="Engineering", code="ENG", description="Software & Tech")
    dept2 = Department(name="Design", code="DSN", description="Product Design")
    db.add_all([dept1, dept2])
    db.commit()

    # Add active employees to Engineering
    e1 = Employee(
        first_name="Alice",
        last_name="Smith",
        email="alice@auraworkforce.io",
        department_id=dept1.id,
        salary=Decimal("110000.00"),
        hire_date=date(2022, 1, 1),
        is_active=True,
    )
    # Add inactive employee to Engineering
    e2 = Employee(
        first_name="Bob",
        last_name="Jones",
        email="bob@auraworkforce.io",
        department_id=dept1.id,
        salary=Decimal("95000.00"),
        hire_date=date(2021, 1, 1),
        is_active=False,
    )
    # Add active employee to Design
    e3 = Employee(
        first_name="Carol",
        last_name="White",
        email="carol@auraworkforce.io",
        department_id=dept2.id,
        salary=Decimal("105000.00"),
        hire_date=date(2023, 1, 1),
        is_active=True,
    )
    db.add_all([e1, e2, e3])
    db.commit()

    response = client.get("/api/v1/departments")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    dept_map = {d["code"]: d for d in data}
    # Engineering should only count 1 active employee (Bob is inactive)
    assert dept_map["ENG"]["employee_count"] == 1
    # Design has 1 active employee
    assert dept_map["DSN"]["employee_count"] == 1


def test_get_department_by_id_success(client: TestClient, db: Session):
    """Retrieve an existing department with active employee count."""
    dept = Department(name="Human Resources", code="HR", description="People & Culture")
    db.add(dept)
    db.commit()
    db.refresh(dept)

    response = client.get(f"/api/v1/departments/{dept.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == dept.id
    assert data["code"] == "HR"
    assert data["name"] == "Human Resources"
    assert data["employee_count"] == 0


def test_get_department_by_id_not_found(client: TestClient):
    """Ensure 404 is returned in the consistent error format when department is not found."""
    response = client.get("/api/v1/departments/99999")
    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "NOT_FOUND"
    assert "99999" in data["detail"]


def test_get_department_employees_paginated(client: TestClient, db: Session):
    """Test retrieving employees by department with pagination support."""
    dept = Department(name="Sales", code="SLS")
    role = Role(title="Account Executive", level="Senior")
    db.add_all([dept, role])
    db.commit()

    # Create 7 employees in Sales
    for i in range(1, 8):
        emp = Employee(
            first_name=f"Seller{i}",
            last_name="Salesperson",
            email=f"seller{i}@auraworkforce.io",
            department_id=dept.id,
            salary=Decimal("75000.00"),
            hire_date=date(2023, 2, 1),
            is_active=True,
        )
        db.add(emp)
        db.commit()
        db.refresh(emp)
        db.add(EmployeeRole(employee_id=emp.id, role_id=role.id, is_primary=True))
    db.commit()

    # Request page 1 with size 3
    res_p1 = client.get(f"/api/v1/departments/{dept.id}/employees?page=1&size=3")
    assert res_p1.status_code == 200
    data_p1 = res_p1.json()
    assert data_p1["total"] == 7
    assert data_p1["page"] == 1
    assert data_p1["size"] == 3
    assert data_p1["pages"] == 3
    assert len(data_p1["items"]) == 3
    assert data_p1["items"][0]["department"]["code"] == "SLS"
    assert data_p1["items"][0]["roles"][0]["title"] == "Account Executive"

    # Request page 3 (remaining 1 item)
    res_p3 = client.get(f"/api/v1/departments/{dept.id}/employees?page=3&size=3")
    assert res_p3.status_code == 200
    data_p3 = res_p3.json()
    assert len(data_p3["items"]) == 1


def test_get_department_employees_department_not_found(client: TestClient):
    """Ensure 404 error when querying employees of a non-existent department."""
    response = client.get("/api/v1/departments/99999/employees")
    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "NOT_FOUND"
    assert "99999" in data["detail"]


def test_create_department_success(client: TestClient):
    payload = {
        "name": "Quality Assurance",
        "code": "QA",
        "cost_center": "CC-700",
        "description": "Software Testing & QA",
        "is_active": True,
    }
    r = client.post("/api/v1/departments", json=payload)
    assert r.status_code == 201
    d = r.json()
    assert d["code"] == "QA"
    assert d["name"] == "Quality Assurance"
    assert d["employee_count"] == 0


def test_create_department_duplicate_code_conflict(client: TestClient, db: Session):
    dept = Department(name="Security Operations", code="SEC")
    db.add(dept)
    db.commit()

    r = client.post("/api/v1/departments", json={"name": "Cyber Security", "code": "SEC"})
    assert r.status_code == 409


def test_create_department_duplicate_name_conflict(client: TestClient, db: Session):
    dept = Department(name="Customer Success", code="CS")
    db.add(dept)
    db.commit()

    r = client.post("/api/v1/departments", json={"name": "Customer Success", "code": "CS2"})
    assert r.status_code == 409


def test_update_department_success(client: TestClient, db: Session):
    dept = Department(name="Finance & Accounting", code="FA", cost_center="CC-800")
    db.add(dept)
    db.commit()

    r = client.patch(f"/api/v1/departments/{dept.id}", json={
        "name": "Finance",
        "cost_center": "CC-801",
    })
    assert r.status_code == 200
    d = r.json()
    assert d["name"] == "Finance"
    assert d["cost_center"] == "CC-801"


def test_update_department_duplicate_code_conflict(client: TestClient, db: Session):
    d1 = Department(name="Dept One", code="D1")
    d2 = Department(name="Dept Two", code="D2")
    db.add_all([d1, d2])
    db.commit()

    r = client.patch(f"/api/v1/departments/{d2.id}", json={"code": "D1"})
    assert r.status_code == 409


def test_delete_department_with_active_employees_fails(client: TestClient, db: Session):
    dept = Department(name="Operations", code="OPS")
    db.add(dept)
    db.commit()

    e = Employee(
        first_name="Op",
        last_name="Worker",
        email="op@auraworkforce.io",
        department_id=dept.id,
        salary=Decimal("60000"),
        hire_date=date(2023, 1, 1),
        is_active=True,
    )
    db.add(e)
    db.commit()

    r = client.delete(f"/api/v1/departments/{dept.id}")
    assert r.status_code == 400
    # Employee must NOT be deleted
    assert db.query(Employee).filter(Employee.id == e.id).first() is not None


def test_delete_empty_department_success(client: TestClient, db: Session):
    dept = Department(name="Temporary Dept", code="TEMP")
    db.add(dept)
    db.commit()

    r = client.delete(f"/api/v1/departments/{dept.id}")
    assert r.status_code == 204
    assert client.get(f"/api/v1/departments/{dept.id}").status_code == 404

