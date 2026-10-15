from datetime import date
from decimal import Decimal
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.role import Role, EmployeeRole
from app.models.employee import Employee
from app.models.attendance import Attendance


def test_unique_email_constraint(db: Session):
    """
    Ensure the unique constraint on email prevents duplicate work emails.
    """
    dept = Department(name="Engineering", code="ENG", description="Software Engineering")
    db.add(dept)
    db.commit()

    emp1 = Employee(
        first_name="Ada",
        last_name="Lovelace",
        email="ada.lovelace@auraworkforce.io",
        department_id=dept.id,
        salary=Decimal("120000.00"),
        hire_date=date(2024, 1, 15),
    )
    db.add(emp1)
    db.commit()

    emp2 = Employee(
        first_name="Another",
        last_name="Ada",
        email="ada.lovelace@auraworkforce.io",  # Duplicate email
        department_id=dept.id,
        salary=Decimal("95000.00"),
        hire_date=date(2024, 2, 1),
    )
    db.add(emp2)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_salary_check_constraint(db: Session):
    """
    Ensure the CheckConstraint('salary > 0') rejects zero or negative salary.
    """
    dept = Department(name="Finance", code="FIN", description="Finance & Accounting")
    db.add(dept)
    db.commit()

    # Zero salary
    invalid_emp_zero = Employee(
        first_name="Zero",
        last_name="Salary",
        email="zero@auraworkforce.io",
        department_id=dept.id,
        salary=Decimal("0.00"),
        hire_date=date(2024, 1, 1),
    )
    db.add(invalid_emp_zero)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    # Negative salary
    invalid_emp_neg = Employee(
        first_name="Negative",
        last_name="Salary",
        email="negative@auraworkforce.io",
        department_id=dept.id,
        salary=Decimal("-1000.00"),
        hire_date=date(2024, 1, 1),
    )
    db.add(invalid_emp_neg)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_manager_hierarchy_relationship(db: Session):
    """
    Test self-referential employee-to-manager hierarchy:
    CEO -> Engineering Director -> Senior Engineer.
    """
    dept = Department(name="Product Engineering", code="PRODENG")
    db.add(dept)
    db.commit()

    # 1. Executive (CEO) has no manager (manager_id=None)
    ceo = Employee(
        first_name="Satya",
        last_name="Nadella",
        email="satya@auraworkforce.io",
        department_id=dept.id,
        manager_id=None,
        salary=Decimal("500000.00"),
        hire_date=date(2020, 1, 1),
    )
    db.add(ceo)
    db.commit()

    # 2. Director reports to CEO
    director = Employee(
        first_name="Gwynne",
        last_name="Shotwell",
        email="gwynne@auraworkforce.io",
        department_id=dept.id,
        manager_id=ceo.id,
        salary=Decimal("250000.00"),
        hire_date=date(2021, 3, 15),
    )
    db.add(director)
    db.commit()

    # 3. Engineer reports to Director
    engineer = Employee(
        first_name="Grace",
        last_name="Hopper",
        email="grace@auraworkforce.io",
        department_id=dept.id,
        manager_id=director.id,
        salary=Decimal("150000.00"),
        hire_date=date(2022, 6, 1),
    )
    db.add(engineer)
    db.commit()

    # Refresh instances from database
    db.refresh(ceo)
    db.refresh(director)
    db.refresh(engineer)

    # Verify upward traversal
    assert engineer.manager is not None
    assert engineer.manager.email == "gwynne@auraworkforce.io"
    assert director.manager is not None
    assert director.manager.email == "satya@auraworkforce.io"
    assert ceo.manager is None

    # Verify downward traversal (direct reports collection)
    assert len(ceo.direct_reports) == 1
    assert ceo.direct_reports[0].id == director.id
    assert len(director.direct_reports) == 1
    assert director.direct_reports[0].id == engineer.id
    assert len(engineer.direct_reports) == 0


def test_department_foreign_key_and_relationship(db: Session):
    """
    Verify department relationship and foreign key integrity.
    """
    dept = Department(name="Design", code="DSN", description="UI/UX & Product Design")
    db.add(dept)
    db.commit()

    emp = Employee(
        first_name="Jony",
        last_name="Ive",
        email="jony@auraworkforce.io",
        department_id=dept.id,
        salary=Decimal("180000.00"),
        hire_date=date(2023, 5, 10),
    )
    db.add(emp)
    db.commit()

    db.refresh(dept)
    db.refresh(emp)

    assert emp.department.name == "Design"
    assert len(dept.employees) == 1
    assert dept.employees[0].email == "jony@auraworkforce.io"

    # Attempt to insert employee with non-existent department_id
    invalid_emp = Employee(
        first_name="Ghost",
        last_name="User",
        email="ghost@auraworkforce.io",
        department_id=999999,
        salary=Decimal("50000.00"),
        hire_date=date(2024, 1, 1),
    )
    db.add(invalid_emp)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_multiple_roles_and_unique_assignment(db: Session):
    """
    Verify that an employee can hold multiple roles (primary + functional),
    and duplicate assignment of the same role fails the unique constraint.
    """
    dept = Department(name="Platform", code="PLT")
    role_primary = Role(title="Principal Architect", level="L6")
    role_sec = Role(title="Incident Commander", level="Operational")
    db.add_all([dept, role_primary, role_sec])
    db.commit()

    emp = Employee(
        first_name="Linus",
        last_name="Torvalds",
        email="linus@auraworkforce.io",
        department_id=dept.id,
        salary=Decimal("220000.00"),
        hire_date=date(2020, 10, 1),
    )
    db.add(emp)
    db.commit()

    # Assign multiple roles
    assign1 = EmployeeRole(employee_id=emp.id, role_id=role_primary.id, is_primary=True)
    assign2 = EmployeeRole(employee_id=emp.id, role_id=role_sec.id, is_primary=False)
    db.add_all([assign1, assign2])
    db.commit()

    db.refresh(emp)
    assert len(emp.employee_roles) == 2
    primary_roles = [er for er in emp.employee_roles if er.is_primary]
    assert len(primary_roles) == 1
    assert primary_roles[0].role.title == "Principal Architect"

    # Duplicate role assignment must fail uq_employee_role
    duplicate_assign = EmployeeRole(employee_id=emp.id, role_id=role_primary.id, is_primary=False)
    db.add(duplicate_assign)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_soft_delete_preservation(db: Session):
    """
    Verify soft deletion logic: employee record remains intact
    when is_active is toggled to False.
    """
    dept = Department(name="Human Resources", code="HR")
    db.add(dept)
    db.commit()

    emp = Employee(
        first_name="David",
        last_name="Clark",
        email="david.clark@auraworkforce.io",
        department_id=dept.id,
        salary=Decimal("85000.00"),
        hire_date=date(2023, 2, 1),
        is_active=True,
    )
    db.add(emp)
    db.commit()

    # Perform soft delete
    emp.is_active = False
    db.commit()
    db.refresh(emp)

    # Record still exists in database
    retrieved = db.query(Employee).filter(Employee.id == emp.id).first()
    assert retrieved is not None
    assert retrieved.is_active is False

    # Filtered active queries exclude the soft-deleted record
    active_count = db.query(Employee).filter(Employee.is_active.is_(True)).count()
    assert active_count == 0


def test_unique_department_and_role_constraints(db: Session):
    """
    Verify unique constraints on department name/code and role title.
    """
    dept1 = Department(name="Security", code="SEC")
    db.add(dept1)
    db.commit()

    # Duplicate department code
    dup_dept = Department(name="Information Security", code="SEC")
    db.add(dup_dept)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    # Duplicate role title
    role1 = Role(title="Security Analyst")
    db.add(role1)
    db.commit()

    dup_role = Role(title="Security Analyst")
    db.add(dup_role)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_attendance_explicit_statuses(db: Session):
    """
    Verify attendance logs accurately support ABSENT_LOP, HALF_DAY_UNPAID, and UNPAID_LEAVE.
    """
    dept = Department(name="HR", code="HR_ATT")
    db.add(dept)
    db.commit()

    emp = Employee(
        first_name="Attend",
        last_name="Tester",
        email="attend.tester@auraworkforce.io",
        department_id=dept.id,
        salary=Decimal("60000.00"),
        hire_date=date(2024, 1, 1),
    )
    db.add(emp)
    db.commit()

    statuses = ["ABSENT_LOP", "HALF_DAY_UNPAID", "UNPAID_LEAVE"]
    for i, st in enumerate(statuses, start=1):
        att = Attendance(
            employee_id=emp.id,
            date=date(2026, 6, i),
            status=st,
            hours_worked=Decimal("0.00") if "ABSENT" in st or "UNPAID_LEAVE" in st else Decimal("4.00"),
            notes=f"Explicit status test: {st}",
        )
        db.add(att)
    db.commit()

    saved_att = db.query(Attendance).filter(Attendance.employee_id == emp.id).all()
    saved_statuses = [a.status for a in saved_att]
    for st in statuses:
        assert st in saved_statuses


def test_employee_exit_date_check_constraint(db: Session):
    """
    Ensure the CheckConstraint('exit_date IS NULL OR exit_date >= hire_date') rejects exit_date < hire_date.
    """
    dept = Department(name="Legal", code="LEG")
    db.add(dept)
    db.commit()

    invalid_emp = Employee(
        first_name="Time",
        last_name="Traveler",
        email="time.traveler@auraworkforce.io",
        department_id=dept.id,
        salary=Decimal("90000.00"),
        hire_date=date(2024, 6, 1),
        exit_date=date(2024, 5, 1),  # Before hire date
        is_active=False,
    )
    db.add(invalid_emp)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

