from datetime import date, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.role import Role
from app.models.employee import Employee


@pytest.fixture
def setup_dept_and_role(db: Session):
    """Fixture providing base department and role for API tests."""
    dept = Department(name="Engineering", code="ENG", description="Core Tech")
    role = Role(title="Software Engineer", level="Mid")
    db.add_all([dept, role])
    db.commit()
    db.refresh(dept)
    db.refresh(role)
    return dept, role


def test_create_employee_success(client: TestClient, setup_dept_and_role):
    dept, role = setup_dept_and_role

    payload = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada.lovelace@auraworkforce.io",
        "department_id": dept.id,
        "role_id": role.id,
        "salary": 130000.00,
        "hire_date": str(date.today() - timedelta(days=30)),
    }

    response = client.post("/api/v1/employees", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["first_name"] == "Ada"
    assert data["last_name"] == "Lovelace"
    assert data["email"] == "ada.lovelace@auraworkforce.io"
    assert data["department"]["code"] == "ENG"
    assert len(data["roles"]) == 1
    assert data["roles"][0]["title"] == "Software Engineer"
    assert data["is_active"] is True


def test_create_employee_duplicate_email_conflict(client: TestClient, setup_dept_and_role):
    dept, role = setup_dept_and_role

    payload = {
        "first_name": "Alan",
        "last_name": "Turing",
        "email": "alan.turing@auraworkforce.io",
        "department_id": dept.id,
        "salary": 140000.00,
        "hire_date": str(date.today()),
    }

    # First creation succeeds
    res1 = client.post("/api/v1/employees", json=payload)
    assert res1.status_code == 201

    # Second creation with identical email fails with 409 Conflict
    res2 = client.post("/api/v1/employees", json=payload)
    assert res2.status_code == 409
    data = res2.json()
    assert data["error_code"] == "CONFLICT"
    assert "already exists" in data["detail"]


def test_create_employee_future_hire_date_rejected(client: TestClient, setup_dept_and_role):
    dept, _ = setup_dept_and_role

    payload = {
        "first_name": "Time",
        "last_name": "Traveler",
        "email": "future@auraworkforce.io",
        "department_id": dept.id,
        "salary": 100000.00,
        "hire_date": str(date.today() + timedelta(days=10)),  # Future date
    }

    response = client.post("/api/v1/employees", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "cannot be in the future" in data["detail"]


def test_create_employee_empty_name_rejected(client: TestClient, setup_dept_and_role):
    dept, _ = setup_dept_and_role

    payload = {
        "first_name": "   ",  # Blank name
        "last_name": "Doe",
        "email": "empty.name@auraworkforce.io",
        "department_id": dept.id,
        "salary": 100000.00,
        "hire_date": str(date.today()),
    }

    response = client.post("/api/v1/employees", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "cannot be empty" in data["detail"]


def test_create_employee_invalid_department(client: TestClient):
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@auraworkforce.io",
        "department_id": 99999,  # Non-existent department
        "salary": 90000.00,
        "hire_date": str(date.today()),
    }

    response = client.post("/api/v1/employees", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "BAD_REQUEST"
    assert "does not exist" in data["detail"]


def test_list_employees_pagination_and_search(client: TestClient, db: Session):
    dept1 = Department(name="Engineering", code="ENG")
    dept2 = Department(name="Marketing", code="MKT")
    db.add_all([dept1, dept2])
    db.commit()

    # Create 5 employees
    for i in range(1, 6):
        dept = dept1 if i <= 3 else dept2
        db.add(
            Employee(
                first_name=f"User{i}",
                last_name="Test",
                email=f"user{i}@auraworkforce.io",
                department_id=dept.id,
                salary=Decimal("80000.00"),
                hire_date=date(2023, 1, 1),
            )
        )
    db.commit()

    # 1. Test pagination (page=1, size=2)
    res_p1 = client.get("/api/v1/employees?page=1&size=2")
    assert res_p1.status_code == 200
    data_p1 = res_p1.json()
    assert data_p1["total"] == 5
    assert data_p1["page"] == 1
    assert data_p1["size"] == 2
    assert data_p1["pages"] == 3
    assert len(data_p1["items"]) == 2

    # 2. Test department filter
    res_dept = client.get("/api/v1/employees?department=MKT")
    assert res_dept.status_code == 200
    data_dept = res_dept.json()
    assert data_dept["total"] == 2
    assert all(e["department"]["code"] == "MKT" for e in data_dept["items"])

    # 3. Test search query
    res_search = client.get("/api/v1/employees?q=user3")
    assert res_search.status_code == 200
    data_search = res_search.json()
    assert data_search["total"] == 1
    assert data_search["items"][0]["email"] == "user3@auraworkforce.io"


def test_get_employee_by_id(client: TestClient, setup_dept_and_role, db: Session):
    dept, _ = setup_dept_and_role
    emp = Employee(
        first_name="Katherine",
        last_name="Johnson",
        email="katherine@auraworkforce.io",
        department_id=dept.id,
        salary=Decimal("125000.00"),
        hire_date=date(2022, 5, 1),
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)

    # Found
    res = client.get(f"/api/v1/employees/{emp.id}")
    assert res.status_code == 200
    assert res.json()["email"] == "katherine@auraworkforce.io"

    # Not found
    res_nf = client.get("/api/v1/employees/99999")
    assert res_nf.status_code == 404
    assert res_nf.json()["error_code"] == "NOT_FOUND"


def test_patch_employee(client: TestClient, setup_dept_and_role, db: Session):
    dept, _ = setup_dept_and_role
    emp = Employee(
        first_name="Margaret",
        last_name="Hamilton",
        email="margaret@auraworkforce.io",
        department_id=dept.id,
        salary=Decimal("110000.00"),
        hire_date=date(2021, 6, 1),
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)

    # Partial update
    patch_payload = {
        "salary": 140000.00,
        "first_name": "Dr. Margaret",
    }
    res = client.patch(f"/api/v1/employees/{emp.id}", json=patch_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["first_name"] == "Dr. Margaret"
    assert float(data["salary"]) == 140000.00
    assert data["last_name"] == "Hamilton"

    res_self_mgr = client.patch(f"/api/v1/employees/{emp.id}", json={"manager_id": emp.id})
    assert res_self_mgr.status_code == 400
    assert res_self_mgr.json()["error_code"] == "BAD_REQUEST"


def test_patch_manager_cycle_prevention(client: TestClient, setup_dept_and_role, db: Session):
    dept, _ = setup_dept_and_role
    emp_a = Employee(
        first_name="Alice",
        last_name="Manager",
        email="alice.mgr@auraworkforce.io",
        department_id=dept.id,
        salary=Decimal("150000.00"),
        hire_date=date(2021, 1, 1),
    )
    emp_b = Employee(
        first_name="Bob",
        last_name="Report",
        email="bob.rep@auraworkforce.io",
        department_id=dept.id,
        salary=Decimal("120000.00"),
        hire_date=date(2022, 1, 1),
    )
    db.add_all([emp_a, emp_b])
    db.commit()
    db.refresh(emp_a)
    db.refresh(emp_b)

    # Bob reports to Alice
    client.patch(f"/api/v1/employees/{emp_b.id}", json={"manager_id": emp_a.id})

    # Setting Alice's manager to Bob must fail with 400 circular hierarchy error
    res_cycle = client.patch(f"/api/v1/employees/{emp_a.id}", json={"manager_id": emp_b.id})
    assert res_cycle.status_code == 400
    assert "circular" in res_cycle.json()["detail"].lower()


def test_patch_clear_manager_and_update_location(client: TestClient, setup_dept_and_role, db: Session):
    dept, _ = setup_dept_and_role
    lead = Employee(
        first_name="Lead",
        last_name="Person",
        email="lead.person@auraworkforce.io",
        department_id=dept.id,
        salary=Decimal("150000.00"),
        hire_date=date(2021, 1, 1),
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    emp = Employee(
        first_name="Staff",
        last_name="Member",
        email="staff.member@auraworkforce.io",
        department_id=dept.id,
        manager_id=lead.id,
        salary=Decimal("90000.00"),
        hire_date=date(2022, 1, 1),
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)

    # Update location & employment_type
    res_update = client.patch(f"/api/v1/employees/{emp.id}", json={
        "work_location": "Hyderabad",
        "employment_type": "Contract",
        "manager_id": None,
    })
    assert res_update.status_code == 200
    data = res_update.json()
    assert data["work_location"] == "Hyderabad"
    assert data["employment_type"] == "Contract"
    assert data["manager_id"] is None


def test_delete_employee_soft_delete(client: TestClient, setup_dept_and_role, db: Session):
    dept, _ = setup_dept_and_role
    emp = Employee(
        first_name="Temporary",
        last_name="Worker",
        email="temp@auraworkforce.io",
        department_id=dept.id,
        salary=Decimal("60000.00"),
        hire_date=date(2023, 1, 1),
        is_active=True,
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)

    # Soft delete
    res_del = client.delete(f"/api/v1/employees/{emp.id}")
    assert res_del.status_code == 204

    # Default list excludes soft-deleted record
    res_list = client.get("/api/v1/employees")
    assert res_list.status_code == 200
    ids = [e["id"] for e in res_list.json()["items"]]
    assert emp.id not in ids

    # Record still exists and can be retrieved directly showing is_active=False and exit_date set
    res_get = client.get(f"/api/v1/employees/{emp.id}")
    assert res_get.status_code == 200
    assert res_get.json()["is_active"] is False
    assert res_get.json()["exit_date"] is not None


def test_assign_inactive_manager_fails(client: TestClient, setup_dept_and_role, db: Session):
    dept, _ = setup_dept_and_role
    inactive_mgr = Employee(
        first_name="Old",
        last_name="Manager",
        email="old.mgr@auraworkforce.io",
        department_id=dept.id,
        salary=Decimal("120000.00"),
        hire_date=date(2021, 1, 1),
        is_active=False,
    )
    db.add(inactive_mgr)
    db.commit()
    db.refresh(inactive_mgr)

    payload = {
        "first_name": "New",
        "last_name": "Joiner",
        "email": "new.joiner@auraworkforce.io",
        "department_id": dept.id,
        "manager_id": inactive_mgr.id,
        "salary": 90000.0,
        "hire_date": "2024-01-01",
    }
    res = client.post("/api/v1/employees", json=payload)
    assert res.status_code == 400
    assert "inactive" in res.json()["detail"].lower()


def test_get_employee_team(client: TestClient, setup_dept_and_role, db: Session):
    dept, _ = setup_dept_and_role

    lead = Employee(
        first_name="Lead",
        last_name="Developer",
        email="lead@auraworkforce.io",
        department_id=dept.id,
        salary=Decimal("150000.00"),
        hire_date=date(2020, 1, 1),
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    report1 = Employee(
        first_name="Junior",
        last_name="One",
        email="jr1@auraworkforce.io",
        department_id=dept.id,
        manager_id=lead.id,
        salary=Decimal("80000.00"),
        hire_date=date(2022, 1, 1),
    )
    report2 = Employee(
        first_name="Junior",
        last_name="Two",
        email="jr2@auraworkforce.io",
        department_id=dept.id,
        manager_id=lead.id,
        salary=Decimal("85000.00"),
        hire_date=date(2022, 2, 1),
    )
    db.add_all([report1, report2])
    db.commit()

    res = client.get(f"/api/v1/employees/{lead.id}/team")
    assert res.status_code == 200
    data = res.json()
    assert data["manager"]["id"] == lead.id
    assert data["total_reports"] == 2
    report_emails = [r["email"] for r in data["direct_reports"]]
    assert "jr1@auraworkforce.io" in report_emails
    assert "jr2@auraworkforce.io" in report_emails


def _emp(db, dept, email, **kw):
    params = dict(
        first_name="T",
        last_name="User",
        email=email,
        department_id=dept.id,
        salary=Decimal("100000"),
        hire_date=date(2022, 1, 1),
    )
    params.update(kw)
    e = Employee(**params)
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


def test_deactivate_sets_status_and_exit_date(client, setup_dept_and_role, db):
    dept, _ = setup_dept_and_role
    e = _emp(db, dept, "a@auraworkforce.io")
    r = client.patch(f"/api/v1/employees/{e.id}", json={"is_active": False})
    assert r.status_code == 200
    d = r.json()
    assert d["employment_status"] == "Deactivated"
    assert d["exit_date"] is not None and d["exit_type"] is None


def test_reactivate_clears_exit_fields(client, setup_dept_and_role, db):
    dept, _ = setup_dept_and_role
    e = _emp(db, dept, "b@auraworkforce.io", is_active=False, employment_status="Resigned",
             exit_date=date(2024, 1, 1), exit_type="Voluntary", exit_reason="Compensation")
    r = client.patch(f"/api/v1/employees/{e.id}", json={"is_active": True})
    d = r.json()
    assert d["employment_status"] == "Active"
    assert d["exit_date"] is None and d["exit_type"] is None and d["exit_reason"] is None


def test_conflicting_status_and_active_rejected(client, setup_dept_and_role, db):
    dept, _ = setup_dept_and_role
    e = _emp(db, dept, "c@auraworkforce.io")
    r = client.patch(f"/api/v1/employees/{e.id}",
                     json={"employment_status": "Resigned", "is_active": True})
    assert r.status_code == 422


def test_invalid_status_rejected(client, setup_dept_and_role, db):
    dept, _ = setup_dept_and_role
    e = _emp(db, dept, "d@auraworkforce.io")
    r = client.patch(f"/api/v1/employees/{e.id}", json={"employment_status": "foo"})
    assert r.status_code == 422


def test_exit_fields_on_active_employee_rejected(client, setup_dept_and_role, db):
    dept, _ = setup_dept_and_role
    e = _emp(db, dept, "e@auraworkforce.io")
    r = client.patch(f"/api/v1/employees/{e.id}", json={"exit_type": "Voluntary"})
    assert r.status_code == 400


def test_soft_delete_does_not_invent_exit_type(client, setup_dept_and_role, db):
    dept, _ = setup_dept_and_role
    e = _emp(db, dept, "f@auraworkforce.io")
    assert client.delete(f"/api/v1/employees/{e.id}").status_code == 204
    d = client.get(f"/api/v1/employees/{e.id}").json()
    assert d["employment_status"] == "Deactivated"
    assert d["exit_type"] is None and d["exit_reason"] is None


def test_explicit_exit_date_is_saved(client, setup_dept_and_role, db):
    dept, _ = setup_dept_and_role
    e = _emp(db, dept, "g@auraworkforce.io")
    r = client.patch(f"/api/v1/employees/{e.id}", json={
        "employment_status": "Resigned", "exit_type": "Voluntary", "exit_date": "2026-03-31"})
    d = r.json()
    assert d["is_active"] is False and d["exit_date"] == "2026-03-31"


def test_create_active_with_exit_type_rejected(client, setup_dept_and_role):
    dept, _ = setup_dept_and_role
    payload = {
        "first_name": "Active",
        "last_name": "WithExit",
        "email": "active_exit@auraworkforce.io",
        "department_id": dept.id,
        "salary": 90000,
        "hire_date": "2024-01-01",
        "is_active": True,
        "exit_type": "Voluntary",
    }
    r = client.post("/api/v1/employees", json=payload)
    assert r.status_code == 422


def test_create_conflicting_status_and_active_rejected(client, setup_dept_and_role):
    dept, _ = setup_dept_and_role
    payload = {
        "first_name": "Conflict",
        "last_name": "Status",
        "email": "conflict_status@auraworkforce.io",
        "department_id": dept.id,
        "salary": 90000,
        "hire_date": "2024-01-01",
        "is_active": True,
        "employment_status": "Resigned",
    }
    r = client.post("/api/v1/employees", json=payload)
    assert r.status_code == 422


def test_patch_exit_date_before_hire_date_rejected(client, setup_dept_and_role, db):
    dept, _ = setup_dept_and_role
    e = _emp(db, dept, "bad_exit_date@auraworkforce.io", hire_date=date(2023, 1, 1))
    r = client.patch(f"/api/v1/employees/{e.id}", json={
        "employment_status": "Resigned",
        "exit_type": "Voluntary",
        "exit_date": "2020-01-01",
    })
    assert r.status_code == 400


def test_patch_inactive_employee_preserves_exit_fields(client, setup_dept_and_role, db):
    dept, _ = setup_dept_and_role
    e = _emp(db, dept, "inactive_patch@auraworkforce.io", is_active=False,
             employment_status="Resigned", exit_date=date(2025, 6, 1),
             exit_type="Voluntary", exit_reason="Personal reasons")
    r = client.patch(f"/api/v1/employees/{e.id}", json={"work_location": "Remote"})
    assert r.status_code == 200
    d = r.json()
    assert d["is_active"] is False
    assert d["work_location"] == "Remote"
    assert d["employment_status"] == "Resigned"
    assert d["exit_date"] == "2025-06-01"
    assert d["exit_type"] == "Voluntary"
    assert d["exit_reason"] == "Personal reasons"


def test_create_exit_date_before_hire_date_rejected(client, setup_dept_and_role):
    dept, _ = setup_dept_and_role
    payload = {
        "first_name": "Bad",
        "last_name": "Date",
        "email": "bad_date@auraworkforce.io",
        "department_id": dept.id,
        "salary": 90000,
        "hire_date": "2024-01-01",
        "exit_date": "2023-01-01",
        "is_active": False,
        "employment_status": "Resigned",
    }
    r = client.post("/api/v1/employees", json=payload)
    assert r.status_code == 422

