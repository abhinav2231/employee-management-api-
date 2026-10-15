import os
import re
import pandas as pd
import pytest
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.assignment import EmployeeAssignment
from app.models.salary_revision import SalaryRevision
from app.models.salary_structure import SalaryStructure
from app.models.attendance import Attendance
from scripts.data_pipeline import load_and_clean_master_dataset
from scripts.seed import seed_database
from scripts.export_csv import export_database_to_csv


@pytest.fixture(scope="session")
def master_dataset():
    return load_and_clean_master_dataset()


def test_master_dataset_cleaning(master_dataset):
    assert len(master_dataset["departments"]) == 11
    assert len(master_dataset["roles"]) == 58
    assert len(master_dataset["employees"]) == 745
    assert len(master_dataset["salary_structures"]) == 12295
    assert len(master_dataset["attendance"]) == 150155
    assert len(master_dataset["assignments"]) == 1606
    assert len(master_dataset["salary_revisions"]) == 2459

    for emp in master_dataset["employees"]:
        assert "@znova-demo.example" in emp["work_email"]
        assert emp["phone_number"] is not None
        assert emp["phone_number"].startswith("+91")
        assert len(emp["phone_number"]) == 13
        assert emp["salary"] > 0
        assert emp["employment_status"] is not None
        assert emp["work_mode"] in ["Hybrid", "Remote", "Onsite"]


def test_faker_fixed_seed_repeatability():
    run1 = load_and_clean_master_dataset()
    run2 = load_and_clean_master_dataset()

    emp1 = run1["employees"][0]
    emp2 = run2["employees"][0]

    assert emp1["employee_id"] == emp2["employee_id"]
    assert emp1["first_name"] == emp2["first_name"]
    assert emp1["last_name"] == emp2["last_name"]
    assert emp1["work_email"] == emp2["work_email"]
    assert emp1["phone_number"] == emp2["phone_number"]
    assert emp1["salary"] == emp2["salary"]


def test_no_test123_dummy_data(master_dataset):
    for emp in master_dataset["employees"][:100]:
        full_name = f"{emp['first_name']} {emp['last_name']}"
        assert not re.search(r"test\d*", full_name, re.IGNORECASE)
        assert not re.search(r"dummy|sample|fake|foo|bar", full_name, re.IGNORECASE)
        assert "@znova-demo.example" in emp["work_email"]
        assert len(emp["first_name"]) >= 2
        assert len(emp["last_name"]) >= 2
        assert emp["salary"] > 0
        assert emp["phone_number"] is not None


def test_linked_relational_integrity(master_dataset):
    valid_codes = {e["employee_id"] for e in master_dataset["employees"]}
    valid_statuses = [
        "PRESENT",
        "WFH",
        "REMOTE",
        "PAID_LEAVE",
        "UNPAID_LEAVE",
        "HALF_DAY",
        "ABSENT",
        "ABSENT_LOP",
        "HALF_DAY_UNPAID",
    ]

    for struct in master_dataset["salary_structures"][:500]:
        assert struct["employee_id"] in valid_codes
        assert struct["monthly_amount"] >= 0

    for att in master_dataset["attendance"][:500]:
        assert att["employee_id"] in valid_codes
        assert att["status"] in valid_statuses
        if att.get("data_quality_flag"):
            assert "NAN" not in att["data_quality_flag"]


def test_idempotent_seeding(db: Session):
    summary1 = seed_database(reset=False, db=db, do_export=False)
    emp_count_run1 = db.query(Employee).count()
    asg_count_run1 = db.query(EmployeeAssignment).count()
    rev_count_run1 = db.query(SalaryRevision).count()
    struct1 = db.query(SalaryStructure).count()
    att1 = db.query(Attendance).count()

    summary2 = seed_database(reset=False, db=db, do_export=False)
    emp_count_run2 = db.query(Employee).count()
    asg_count_run2 = db.query(EmployeeAssignment).count()
    rev_count_run2 = db.query(SalaryRevision).count()
    struct2 = db.query(SalaryStructure).count()
    att2 = db.query(Attendance).count()

    assert emp_count_run1 == emp_count_run2 == 745
    assert asg_count_run1 == asg_count_run2 == 1606
    assert rev_count_run1 == rev_count_run2 == 2459
    assert struct1 == struct2 == 12295
    assert att1 == att2 == 150155
    assert summary2["employees_inserted"] == 0


def test_csv_exports_valid(db: Session, tmp_path):
    seed_database(reset=False, db=db, do_export=False)
    result = export_database_to_csv(output_dir=str(tmp_path), db=db)
    assert os.path.exists(result["employees_csv"])
    assert os.path.exists(result["salary_structures_csv"])
    assert os.path.exists(result["attendance_csv"])
    assert os.path.exists(result["salary_revisions_csv"])
    assert os.path.exists(result["assignments_csv"])

    emp_df = pd.read_csv(result["employees_csv"])
    assert "employee_id" in emp_df.columns
    assert "work_email" in emp_df.columns
    assert "salary" in emp_df.columns
    assert len(emp_df) == 745

    struct_df = pd.read_csv(result["salary_structures_csv"])
    assert "employee_id" in struct_df.columns
    assert "component_name" in struct_df.columns
    assert "monthly_amount" in struct_df.columns
    assert len(struct_df) == 12295

    att_df = pd.read_csv(result["attendance_csv"])
    assert "employee_id" in att_df.columns
    assert "status" in att_df.columns
    assert len(att_df) == 150155

    rev_df = pd.read_csv(result["salary_revisions_csv"])
    assert "revision_id" in rev_df.columns
    assert "employee_id" in rev_df.columns
    assert len(rev_df) == 2459

    asgn_df = pd.read_csv(result["assignments_csv"])
    assert "assignment_id" in asgn_df.columns
    assert "employee_id" in asgn_df.columns
    assert len(asgn_df) == 1606

