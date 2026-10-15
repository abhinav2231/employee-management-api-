from datetime import date, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.role import Role, EmployeeRole
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


def test_create_and_retrieve_employee_with_phone(client, setup_dept_and_role):
    dept, role = setup_dept_and_role
    payload = {
        "first_name": "Rohan",
        "last_name": "Sharma",
        "email": "rohan.sharma@auraworkforce.io",
        "phone_number": "+919876543210",
        "department_id": dept.id,
        "role_id": role.id,
        "salary": 120000,
        "hire_date": "2024-03-01",
        "is_active": True,
    }
    r = client.post("/api/v1/employees", json=payload)
    assert r.status_code == 201
    d = r.json()
    assert d["phone_number"] == "+919876543210"

    emp_id = d["id"]
    get_res = client.get(f"/api/v1/employees/{emp_id}")
    assert get_res.status_code == 200
    assert get_res.json()["phone_number"] == "+919876543210"


def test_patch_employee_phone_number(client, setup_dept_and_role, db):
    dept, _ = setup_dept_and_role
    e = _emp(db, dept, "phone_patch@auraworkforce.io", phone_number="+918888888888")
    r = client.patch(f"/api/v1/employees/{e.id}", json={"phone_number": "+919999999999"})
    assert r.status_code == 200
    assert r.json()["phone_number"] == "+919999999999"

    get_res = client.get(f"/api/v1/employees/{e.id}")
    assert get_res.json()["phone_number"] == "+919999999999"


def test_create_employee_in_inactive_department_fails(client: TestClient, db: Session):
    inactive_dept = Department(name="Retired Department", code="RET", is_active=False)
    db.add(inactive_dept)
    db.commit()

    payload = {
        "first_name": "New",
        "last_name": "Hire",
        "email": "new.hire@auraworkforce.io",
        "department_id": inactive_dept.id,
        "salary": 90000,
        "hire_date": "2024-01-01",
    }
    r = client.post("/api/v1/employees", json=payload)
    assert r.status_code == 400
    assert "inactive" in r.json()["detail"].lower()


def test_patch_employee_to_inactive_department_fails(client: TestClient, setup_dept_and_role, db: Session):
    active_dept, _ = setup_dept_and_role
    inactive_dept = Department(name="Closed Branch", code="CLS", is_active=False)
    db.add(inactive_dept)
    db.commit()

    e = _emp(db, active_dept, "transfer_test@auraworkforce.io")
    r = client.patch(f"/api/v1/employees/{e.id}", json={"department_id": inactive_dept.id})
    assert r.status_code == 400
    assert "inactive" in r.json()["detail"].lower()


def test_employee_invalid_phone_number_format_rejected(client: TestClient, setup_dept_and_role, db: Session):
    dept, _ = setup_dept_and_role
    base_payload = {
        "first_name": "Phone",
        "last_name": "Tester",
        "email": "phone.tester@auraworkforce.io",
        "department_id": dept.id,
        "salary": 80000,
        "hire_date": "2024-01-01",
    }

    # Missing +91
    r1 = client.post("/api/v1/employees", json={**base_payload, "phone_number": "9876543210"})
    assert r1.status_code == 422

    # First digit after +91 is 5 (must be 6-9)
    r2 = client.post("/api/v1/employees", json={**base_payload, "phone_number": "+915876543210"})
    assert r2.status_code == 422

    # Patch with invalid phone
    e = _emp(db, dept, "phone_patch_inv@auraworkforce.io")
    r3 = client.patch(f"/api/v1/employees/{e.id}", json={"phone_number": "invalid-phone"})
    assert r3.status_code == 422


def test_list_employees_escapes_like_wildcards(client: TestClient, db: Session):
    dept1 = Department(name="Dept_Special", code="D_SP")
    dept2 = Department(name="Dept-Special", code="D-SP")
    db.add_all([dept1, dept2])
    db.commit()

    e1 = _emp(db, dept1, "e1_special@auraworkforce.io", employee_code="EMP_001", first_name="John_1")
    e2 = _emp(db, dept2, "e2_special@auraworkforce.io", employee_code="EMP-001", first_name="John-1")

    # Filter with employee_code containing '_' must not match '-'
    res_code = client.get("/api/v1/employees?employee_code=EMP_001")
    assert res_code.status_code == 200
    items_code = res_code.json()["items"]
    assert len(items_code) == 1
    assert items_code[0]["employee_code"] == "EMP_001"

    # Search with q containing '_' must not match '-'
    res_q = client.get("/api/v1/employees?q=John_1")
    assert res_q.status_code == 200
    items_q = res_q.json()["items"]
    assert len(items_q) == 1
    assert items_q[0]["first_name"] == "John_1"

    # Search with department containing '_'
    res_dept = client.get("/api/v1/employees?department=Dept_Special")
    assert res_dept.status_code == 200
    items_dept = res_dept.json()["items"]
    assert len(items_dept) == 1
    assert items_dept[0]["email"] == "e1_special@auraworkforce.io"


def test_list_employees_include_inactive(client: TestClient, db: Session):
    dept = Department(name="Ops", code="OPS")
    db.add(dept)
    db.commit()

    active_emp = _emp(db, dept, "active.worker@auraworkforce.io", is_active=True)
    inactive_emp = _emp(db, dept, "inactive.worker@auraworkforce.io", is_active=False)

    # By default, only active employees are returned
    res_default = client.get("/api/v1/employees")
    assert res_default.status_code == 200
    ids_default = [item["id"] for item in res_default.json()["items"]]
    assert active_emp.id in ids_default
    assert inactive_emp.id not in ids_default

    # With include_inactive=true, both active and inactive are returned
    res_all = client.get("/api/v1/employees?include_inactive=true")
    assert res_all.status_code == 200
    ids_all = [item["id"] for item in res_all.json()["items"]]
    assert active_emp.id in ids_all
    assert inactive_emp.id in ids_all


def test_employees_and_departments_pagination_edges(client: TestClient, db: Session):
    dept = Department(name="PaginationDept", code="PAG")
    db.add(dept)
    db.commit()
    _emp(db, dept, "p1@auraworkforce.io")
    _emp(db, dept, "p2@auraworkforce.io")

    # Page past the end -> returns empty items list, 200 OK
    res_past = client.get("/api/v1/employees?page=999&size=10")
    assert res_past.status_code == 200
    assert res_past.json()["items"] == []
    assert res_past.json()["page"] == 999

    res_dept_past = client.get(f"/api/v1/departments/{dept.id}/employees?page=999&size=10")
    assert res_dept_past.status_code == 200
    assert res_dept_past.json()["items"] == []

    # size = 0 -> 422
    assert client.get("/api/v1/employees?size=0").status_code == 422
    assert client.get(f"/api/v1/departments/{dept.id}/employees?size=0").status_code == 422

    # size = 101 -> 422
    assert client.get("/api/v1/employees?size=101").status_code == 422
    assert client.get(f"/api/v1/departments/{dept.id}/employees?size=101").status_code == 422


def test_delete_employee_reparents_reports(client: TestClient, db: Session):
    dept = Department(name="HierarchyDept", code="HIER")
    db.add(dept)
    db.commit()

    grand_mgr = _emp(db, dept, "grand.mgr@auraworkforce.io")
    mgr = _emp(db, dept, "mid.mgr@auraworkforce.io", manager_id=grand_mgr.id)
    report = _emp(db, dept, "direct.rep@auraworkforce.io", manager_id=mgr.id)

    # DELETE manager
    del_res = client.delete(f"/api/v1/employees/{mgr.id}")
    assert del_res.status_code == 204

    db.refresh(report)
    assert report.manager_id == grand_mgr.id


def test_patch_deactivate_reparents_reports(client: TestClient, db: Session):
    dept = Department(name="PatchReparentDept", code="PRP")
    db.add(dept)
    db.commit()

    # Case 1: is_active = False
    gm1 = _emp(db, dept, "gm1@auraworkforce.io")
    mgr1 = _emp(db, dept, "mgr1@auraworkforce.io", manager_id=gm1.id)
    rep1 = _emp(db, dept, "rep1@auraworkforce.io", manager_id=mgr1.id)

    patch_res1 = client.patch(f"/api/v1/employees/{mgr1.id}", json={"is_active": False})
    assert patch_res1.status_code == 200
    db.refresh(rep1)
    assert rep1.manager_id == gm1.id

    # Case 2: employment_status = "Resigned"
    gm2 = _emp(db, dept, "gm2@auraworkforce.io")
    mgr2 = _emp(db, dept, "mgr2@auraworkforce.io", manager_id=gm2.id)
    rep2 = _emp(db, dept, "rep2@auraworkforce.io", manager_id=mgr2.id)

    patch_res2 = client.patch(f"/api/v1/employees/{mgr2.id}", json={"employment_status": "Resigned"})
    assert patch_res2.status_code == 200
    db.refresh(rep2)
    assert rep2.manager_id == gm2.id


def test_duplicate_custom_employee_code_conflict(client: TestClient, db: Session):
    dept = Department(name="CodeDept", code="CDE")
    db.add(dept)
    db.commit()

    payload1 = {
        "employee_code": "EMP-0888",
        "first_name": "Unique",
        "last_name": "One",
        "email": "unique.one@auraworkforce.io",
        "department_id": dept.id,
        "salary": 75000,
        "hire_date": "2024-01-01",
    }
    r1 = client.post("/api/v1/employees", json=payload1)
    assert r1.status_code == 201

    payload2 = {
        "employee_code": "EMP-0888",
        "first_name": "Unique",
        "last_name": "Two",
        "email": "unique.two@auraworkforce.io",
        "department_id": dept.id,
        "salary": 80000,
        "hire_date": "2024-01-01",
    }
    r2 = client.post("/api/v1/employees", json=payload2)
    assert r2.status_code == 409
    assert r2.json()["field"] == "employee_code"


def test_custom_employee_code_format_validation(client: TestClient, db: Session):
    dept = Department(name="FmtDept", code="FMT")
    db.add(dept)
    db.commit()

    base_payload = {
        "first_name": "Invalid",
        "last_name": "Code",
        "email": "invalid.code@auraworkforce.io",
        "department_id": dept.id,
        "salary": 70000,
        "hire_date": "2024-01-01",
    }

    # EMP-99999999 exceeds 4 digits
    res1 = client.post("/api/v1/employees", json={**base_payload, "employee_code": "EMP-99999999"})
    assert res1.status_code == 422
    assert "EMP-XXXX" in res1.json()["detail"]
    assert not res1.json()["detail"].startswith("Value error, ")

    # Non-standard prefix
    res2 = client.post("/api/v1/employees", json={**base_payload, "employee_code": "WRONG-0001"})
    assert res2.status_code == 422


def test_email_case_insensitivity_create_and_update(client: TestClient, db: Session):
    dept = Department(name="CaseDept", code="CSE")
    db.add(dept)
    db.commit()

    # Create with mixed-case email -> saved as lowercase
    res1 = client.post("/api/v1/employees", json={
        "first_name": "Case",
        "last_name": "Test",
        "email": "Case.Test@AuraWorkforce.IO",
        "department_id": dept.id,
        "salary": 90000,
        "hire_date": "2024-01-01",
    })
    assert res1.status_code == 201
    assert res1.json()["email"] == "case.test@auraworkforce.io"

    # Creating another employee with different casing of the same email -> 409
    res2 = client.post("/api/v1/employees", json={
        "first_name": "Another",
        "last_name": "Case",
        "email": "CASE.TEST@auraworkforce.io",
        "department_id": dept.id,
        "salary": 85000,
        "hire_date": "2024-01-01",
    })
    assert res2.status_code == 409
    assert res2.json()["field"] == "email"


def test_patch_employee_switch_primary_role(client: TestClient, db: Session):
    dept = Department(name="RoleSwitchDept", code="RSD")
    r1 = Role(title="Software Engineer", code="SWE")
    r2 = Role(title="Senior Software Engineer", code="SR_SWE")
    db.add_all([dept, r1, r2])
    db.commit()

    emp = _emp(db, dept, "role.switcher@auraworkforce.io")
    er1 = EmployeeRole(employee_id=emp.id, role_id=r1.id, is_primary=True)
    db.add(er1)
    db.commit()

    # Switch primary role to r2
    res = client.patch(f"/api/v1/employees/{emp.id}", json={"role_id": r2.id})
    assert res.status_code == 200

    db.refresh(emp)
    primary_roles = [er for er in emp.employee_roles if er.is_primary]
    assert len(primary_roles) == 1
    assert primary_roles[0].role_id == r2.id


def test_patch_employee_writes_history_tables(client: TestClient, db: Session):
    from app.models.salary_revision import SalaryRevision
    from app.models.assignment import EmployeeAssignment

    dept1 = Department(name="DeptA", code="DA")
    dept2 = Department(name="DeptB", code="DB")
    db.add_all([dept1, dept2])
    db.commit()

    emp = _emp(db, dept1, "history.tester@auraworkforce.io", salary=Decimal("100000.00"))

    # Initial history count
    rev_count_before = db.query(SalaryRevision).filter(SalaryRevision.employee_id == emp.id).count()
    asg_count_before = db.query(EmployeeAssignment).filter(EmployeeAssignment.employee_id == emp.id).count()

    # Update salary -> writes SalaryRevision
    res_sal = client.patch(f"/api/v1/employees/{emp.id}", json={"salary": 120000})
    assert res_sal.status_code == 200
    rev_after = db.query(SalaryRevision).filter(SalaryRevision.employee_id == emp.id).all()
    assert len(rev_after) == rev_count_before + 1
    latest_rev = rev_after[-1]
    assert latest_rev.new_annual_fixed == Decimal("120000.00")
    assert latest_rev.previous_annual_fixed == Decimal("100000.00")

    # Update department -> writes EmployeeAssignment
    res_dept = client.patch(f"/api/v1/employees/{emp.id}", json={"department_id": dept2.id})
    assert res_dept.status_code == 200
    asg_after = db.query(EmployeeAssignment).filter(EmployeeAssignment.employee_id == emp.id).all()
    assert len(asg_after) == asg_count_before + 1
    latest_asg = asg_after[-1]
    assert latest_asg.department_id == dept2.id


def test_department_employees_include_inactive(client: TestClient, db: Session):
    dept = Department(name="RosterDept", code="RST")
    db.add(dept)
    db.commit()

    e_active = _emp(db, dept, "active.roster@auraworkforce.io", is_active=True)
    e_inactive = _emp(db, dept, "inactive.roster@auraworkforce.io", is_active=False)

    res_active_only = client.get(f"/api/v1/departments/{dept.id}/employees")
    assert res_active_only.status_code == 200
    ids_active_only = [item["id"] for item in res_active_only.json()["items"]]
    assert e_active.id in ids_active_only
    assert e_inactive.id not in ids_active_only

    res_all = client.get(f"/api/v1/departments/{dept.id}/employees?include_inactive=true")
    assert res_all.status_code == 200
    ids_all = [item["id"] for item in res_all.json()["items"]]
    assert e_active.id in ids_all
    assert e_inactive.id in ids_all


def test_roles_listing_endpoint(client: TestClient, db: Session):
    role = Role(title="Cloud Architect", code="CA_01")
    db.add(role)
    db.commit()

    res = client.get("/api/v1/roles")
    assert res.status_code == 200
    titles = [r["title"] for r in res.json()]
    assert "Cloud Architect" in titles

    res_single = client.get(f"/api/v1/roles/{role.id}")
    assert res_single.status_code == 200
    assert res_single.json()["code"] == "CA_01"


def test_health_ready_checks_database(client: TestClient):
    res_top = client.get("/health/ready")
    assert res_top.status_code == 200
    assert res_top.json()["status"] == "ok"
    assert res_top.json()["database"] == "connected"

    res_v1 = client.get("/api/v1/health/ready")
    assert res_v1.status_code == 200
    assert res_v1.json()["status"] == "ok"





