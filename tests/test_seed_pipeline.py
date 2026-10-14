import os
import re
import pandas as pd
import pytest
from sqlalchemy.orm import Session

from app.models.employee import Employee
from scripts.data_pipeline import load_and_clean_master_dataset
from scripts.seed import seed_database
from scripts.export_csv import export_database_to_csv


def test_master_dataset_cleaning():
    dataset = load_and_clean_master_dataset()
    assert len(dataset["departments"]) == 11
    assert len(dataset["roles"]) == 58
    assert len(dataset["employees"]) == 745
    assert len(dataset["salaries"]) > 1000
    assert len(dataset["attendance"]) > 10000

    for emp in dataset["employees"]:
        assert "@auraworkforce.io" in emp["email"]
        assert emp["phone_number"] is not None
        assert emp["salary"] > 0


def test_faker_fixed_seed_repeatability():
    run1 = load_and_clean_master_dataset()
    run2 = load_and_clean_master_dataset()

    emp1 = run1["employees"][0]
    emp2 = run2["employees"][0]

    assert emp1["employee_code"] == emp2["employee_code"]
    assert emp1["first_name"] == emp2["first_name"]
    assert emp1["last_name"] == emp2["last_name"]
    assert emp1["email"] == emp2["email"]
    assert emp1["phone_number"] == emp2["phone_number"]
    assert emp1["salary"] == emp2["salary"]


def test_no_test123_dummy_data():
    dataset = load_and_clean_master_dataset()
    for emp in dataset["employees"][:100]:
        full_name = f"{emp['first_name']} {emp['last_name']}"
        assert not re.search(r"test\d*", full_name, re.IGNORECASE)
        assert not re.search(r"dummy|sample|fake|foo|bar", full_name, re.IGNORECASE)
        assert "@auraworkforce.io" in emp["email"]
        assert len(emp["first_name"]) >= 2
        assert len(emp["last_name"]) >= 2
        assert emp["salary"] > 0
        assert emp["phone_number"] is not None


def test_linked_relational_integrity():
    dataset = load_and_clean_master_dataset()
    valid_codes = {e["employee_code"] for e in dataset["employees"]}

    for sal in dataset["salaries"][:500]:
        assert sal["employee_code"] in valid_codes
        assert sal["base_salary"] > 0
        assert sal["net_salary"] > 0

    for att in dataset["attendance"][:500]:
        assert att["employee_code"] in valid_codes
        assert att["status"] in ["PRESENT", "REMOTE", "PAID_LEAVE", "UNPAID_LEAVE", "HALF_DAY", "ABSENT"]


def test_idempotent_seeding(db: Session):
    summary1 = seed_database(reset=False, db=db)
    emp_count_run1 = db.query(Employee).count()

    summary2 = seed_database(reset=False, db=db)
    emp_count_run2 = db.query(Employee).count()

    assert emp_count_run1 == emp_count_run2
    assert summary2["employees_inserted"] == 0
    assert emp_count_run1 == 745


def test_csv_exports_valid(db: Session):
    seed_database(reset=False, db=db)
    result = export_database_to_csv(db=db)
    assert os.path.exists(result["employees_csv"])
    assert os.path.exists(result["salaries_csv"])
    assert os.path.exists(result["attendance_csv"])

    emp_df = pd.read_csv(result["employees_csv"])
    assert "employee_code" in emp_df.columns
    assert "manager_code" in emp_df.columns
    assert "email" in emp_df.columns
    assert "salary" in emp_df.columns
    assert len(emp_df) == 745

    sal_df = pd.read_csv(result["salaries_csv"])
    assert "employee_code" in sal_df.columns
    assert "net_salary" in sal_df.columns
    assert len(sal_df) > 0

    att_df = pd.read_csv(result["attendance_csv"])
    assert "employee_code" in att_df.columns
    assert "status" in att_df.columns
    assert len(att_df) > 0
