from datetime import date, datetime, time
from decimal import Decimal
import json
import os
import random
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from faker import Faker

RANDOM_SEED = 42
Faker.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

fake = Faker("en_IN")

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SEED_PATH = os.path.join(_REPO_ROOT, "data", "seed", "01_LedgerForge_Python_Master_Dataset.xlsx")
_DATA_PATH = os.path.join(_REPO_ROOT, "data", "01_LedgerForge_Python_Master_Dataset.xlsx")
MASTER_DATASET_PATH = _SEED_PATH if os.path.exists(_SEED_PATH) else _DATA_PATH

FIXTURES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "tests",
    "fixtures",
)


def parse_time_str(val: Any) -> Optional[str]:
    if val is None or pd.isna(val):
        return None
    if isinstance(val, time):
        return val.strftime("%H:%M")
    if isinstance(val, datetime):
        return val.strftime("%H:%M")
    s = str(val).strip()
    return s if s and s != "nan" else None


def parse_date_val(val: Any) -> Optional[date]:
    if val is None or pd.isna(val):
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    try:
        return pd.to_datetime(val).date()
    except Exception:
        return None


def load_and_clean_master_dataset(
    recent_attendance_months: Optional[int] = None,
    export_payroll_fixture: bool = True,
) -> Dict[str, Any]:
    """Loads and cleans the complete LedgerForge Master Dataset from Excel."""
    if not os.path.exists(MASTER_DATASET_PATH):
        raise FileNotFoundError(f"Master dataset file not found at: {MASTER_DATASET_PATH}")

    fake.seed_instance(RANDOM_SEED)
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    xl = pd.ExcelFile(MASTER_DATASET_PATH)

    # 1. Departments
    df_depts = xl.parse("departments")
    departments = []
    for _, row in df_depts.iterrows():
        dept_id = str(row["department_id"]).strip()
        departments.append({
            "department_id": dept_id,
            "department_name": str(row["department_name"]).strip(),
            "cost_center": str(row["cost_center"]).strip() if pd.notna(row.get("cost_center")) else None,
            "description": str(row["description"]).strip() if pd.notna(row.get("description")) else None,
            "is_active": True,
            # Legacy compatibility keys
            "code": dept_id,
            "name": str(row["department_name"]).strip(),
        })

    # 2. Roles
    df_roles = xl.parse("roles")
    roles = []
    for _, row in df_roles.iterrows():
        role_id = str(row["role_id"]).strip()
        roles.append({
            "role_id": role_id,
            "department_id": str(row["department_id"]).strip() if pd.notna(row.get("department_id")) else None,
            "role_title": str(row["role_title"]).strip(),
            "level": int(row["level"]) if pd.notna(row.get("level")) else None,
            "grade": str(row["grade"]).strip() if pd.notna(row.get("grade")) else None,
            "band_min_annual": int(row["band_min_annual"]) if pd.notna(row.get("band_min_annual")) else None,
            "band_mid_annual": int(row["band_mid_annual"]) if pd.notna(row.get("band_mid_annual")) else None,
            "band_max_annual": int(row["band_max_annual"]) if pd.notna(row.get("band_max_annual")) else None,
            "overtime_eligible": str(row.get("overtime_eligible", "N")).strip().upper(),
            "band_year": int(row["band_year"]) if pd.notna(row.get("band_year")) else 2026,
            "is_active": True,
            # Legacy compatibility keys
            "code": role_id,
            "title": str(row["role_title"]).strip(),
            "department_code": str(row["department_id"]).strip() if pd.notna(row.get("department_id")) else None,
        })

    # 3. Salary Revisions (Map latest salary for employees)
    df_sal_rev = xl.parse("salary_revisions")
    df_sal_sorted = df_sal_rev.sort_values("effective_from")
    latest_salary_map: Dict[str, Decimal] = {}
    salary_revisions = []

    for _, row in df_sal_sorted.iterrows():
        rev_id = str(row["revision_id"]).strip()
        emp_id = str(row["employee_id"]).strip()
        eff_from = parse_date_val(row.get("effective_from"))
        reason = str(row["revision_reason"]).strip() if pd.notna(row.get("revision_reason")) else None
        prev_fixed = Decimal(str(int(row["previous_annual_fixed"]))) if pd.notna(row.get("previous_annual_fixed")) else None
        new_fixed_val = row.get("new_annual_fixed")
        new_fixed = Decimal(str(int(new_fixed_val))) if pd.notna(new_fixed_val) and float(new_fixed_val) > 0 else Decimal("0")
        pct = Decimal(str(round(float(row["pct_change"]), 2))) if pd.notna(row.get("pct_change")) else None
        role_after = str(row["role_id_after"]).strip() if pd.notna(row.get("role_id_after")) else None
        approved = str(row["approved_by"]).strip() if pd.notna(row.get("approved_by")) else None

        if eff_from and new_fixed > 0:
            latest_salary_map[emp_id] = new_fixed
            salary_revisions.append({
                "revision_id": rev_id,
                "revision_code": rev_id,
                "employee_id": emp_id,
                "employee_code": emp_id,
                "effective_from": eff_from,
                "revision_reason": reason,
                "previous_annual_fixed": prev_fixed,
                "new_annual_fixed": new_fixed,
                "pct_change": pct,
                "role_id_after": role_after,
                "approved_by": approved,
            })

    # 4. Employees
    df_emp = xl.parse("employees")
    employees = []

    for _, row in df_emp.iterrows():
        emp_id = str(row["employee_id"]).strip()
        first_name = str(row["first_name"]).strip()
        last_name = str(row["last_name"]).strip()
        full_name = str(row.get("full_name", f"{first_name} {last_name}")).strip()
        work_email = str(row["work_email"]).strip().lower()

        phone_number = "+91" + fake.random_element(["6", "7", "8", "9"]) + fake.numerify("#########")
        hire_date = parse_date_val(row.get("hire_date"))
        exit_date = parse_date_val(row.get("exit_date"))
        dob = parse_date_val(row.get("date_of_birth"))
        resignation_date = parse_date_val(row.get("resignation_date"))

        status_str = str(row.get("employment_status", "Active")).strip()
        is_active = (status_str.lower() == "active")
        exit_type = str(row.get("exit_type")).strip() if pd.notna(row.get("exit_type")) else None
        exit_reason = str(row.get("exit_reason")).strip() if pd.notna(row.get("exit_reason")) else None

        if pd.isna(row.get("work_mode")):
            raise ValueError(f"Missing work_mode for employee '{emp_id}'")
        work_mode = str(row["work_mode"]).strip()

        pf_val = str(row.get("pf_applicable", "Y")).strip().upper()
        pf_applicable = "Y" if pf_val in ["Y", "YES", "TRUE", "1"] else "N"
        esi_val = str(row.get("esi_applicable", "N")).strip().upper()
        esi_applicable = "Y" if esi_val in ["Y", "YES", "TRUE", "1"] else "N"

        if emp_id not in latest_salary_map:
            raise ValueError(f"Missing salary record for employee '{emp_id}'")
        salary = latest_salary_map[emp_id]

        if pd.isna(row.get("department_id")):
            raise ValueError(f"Missing department_id for employee '{emp_id}'")
        dept_id = str(row["department_id"]).strip()

        if pd.isna(row.get("role_id")):
            raise ValueError(f"Missing role_id for employee '{emp_id}'")
        role_id = str(row["role_id"]).strip()
        mgr_id = str(row["manager_id"]).strip() if pd.notna(row.get("manager_id")) else None

        if not hire_date:
            raise ValueError(f"Missing hire_date for employee '{emp_id}'")

        employees.append({
            "employee_id": emp_id,
            "employee_code": emp_id,
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
            "work_email": work_email,
            "email": work_email,
            "phone_number": phone_number,
            "gender": str(row["gender"]).strip() if pd.notna(row.get("gender")) else None,
            "date_of_birth": dob,
            "department_id": dept_id,
            "department_code": dept_id,
            "role_id": role_id,
            "role_code": role_id,
            "manager_id": mgr_id,
            "manager_code": mgr_id,
            "salary": salary,
            "hire_date": hire_date,
            "exit_date": exit_date,
            "employment_status": status_str,
            "employment_type": str(row.get("employment_type", "Permanent")).strip(),
            "exit_type": exit_type,
            "exit_reason": exit_reason,
            "work_location": str(row.get("work_location", "Bengaluru")).strip(),
            "work_mode": work_mode,
            "highest_education": str(row["highest_education"]).strip() if pd.notna(row.get("highest_education")) else None,
            "prior_experience_years": Decimal(str(row["prior_experience_years"])) if pd.notna(row.get("prior_experience_years")) else None,
            "career_gap_months": int(row["career_gap_months"]) if pd.notna(row.get("career_gap_months")) else 0,
            "commute_distance_km": Decimal(str(row["commute_distance_km"])) if pd.notna(row.get("commute_distance_km")) else None,
            "pf_applicable": pf_applicable,
            "esi_applicable": esi_applicable,
            "notice_period_days": int(row["notice_period_days"]) if pd.notna(row.get("notice_period_days")) else 30,
            "resignation_date": resignation_date,
            "is_active": is_active,
        })

    # 5. Employee Assignments
    df_asg = xl.parse("employee_assignments")
    assignments = []
    for _, row in df_asg.iterrows():
        asg_id = str(row["assignment_id"]).strip()
        emp_id = str(row["employee_id"]).strip()
        eff_from = parse_date_val(row.get("effective_from"))
        eff_to = parse_date_val(row.get("effective_to"))
        dept_id = str(row["department_id"]).strip() if pd.notna(row.get("department_id")) else None
        role_id = str(row["role_id"]).strip() if pd.notna(row.get("role_id")) else None
        lvl = int(row["job_level"]) if pd.notna(row.get("job_level")) else None
        mgr_id = str(row["manager_id"]).strip() if pd.notna(row.get("manager_id")) else None
        reason = str(row["change_reason"]).strip() if pd.notna(row.get("change_reason")) else None
        if eff_from:
            assignments.append({
                "assignment_id": asg_id,
                "assignment_code": asg_id,
                "employee_id": emp_id,
                "employee_code": emp_id,
                "effective_from": eff_from,
                "effective_to": eff_to,
                "department_id": dept_id,
                "department_code": dept_id,
                "role_id": role_id,
                "role_code": role_id,
                "job_level": lvl,
                "manager_id": mgr_id,
                "manager_code": mgr_id,
                "change_reason": reason,
            })

    # 6. Salary Structures
    df_struct = xl.parse("salary_structures")
    salary_structures = []
    for _, row in df_struct.iterrows():
        struct_id = str(row["structure_id"]).strip()
        emp_id = str(row["employee_id"]).strip()
        comp_id = str(row["component_id"]).strip()
        comp_name = str(row["component_name"]).strip()
        comp_type = str(row["component_type"]).strip()
        amt = Decimal(str(int(row["monthly_amount"])))
        eff_from = parse_date_val(row.get("effective_from"))
        eff_to = parse_date_val(row.get("effective_to"))
        rev_id = str(row["revision_id"]).strip() if pd.notna(row.get("revision_id")) else None

        salary_structures.append({
            "structure_id": struct_id,
            "employee_id": emp_id,
            "component_id": comp_id,
            "component_name": comp_name,
            "component_type": comp_type,
            "monthly_amount": amt,
            "effective_from": eff_from,
            "effective_to": eff_to,
            "revision_id": rev_id,
        })

    # 7. Attendance
    df_att = xl.parse("attendance")
    if recent_attendance_months:
        max_att_date = pd.to_datetime(df_att["attendance_date"]).max()
        min_att_date = max_att_date - pd.DateOffset(months=recent_attendance_months)
        df_att = df_att[df_att["attendance_date"] >= min_att_date]

    attendance = []
    for _, row in df_att.iterrows():
        att_id = str(row["attendance_id"]).strip()
        emp_id = str(row["employee_id"]).strip()
        att_date = parse_date_val(row.get("attendance_date"))
        weekday = str(row["weekday"]).strip() if pd.notna(row.get("weekday")) else None
        status = str(row["status"]).strip().upper()
        leave_code = str(row["leave_type_code"]).strip() if pd.notna(row.get("leave_type_code")) else None
        check_in = parse_time_str(row.get("check_in"))
        check_out = parse_time_str(row.get("check_out"))
        hours_raw = row.get("hours_worked")
        hours_worked = Decimal(str(round(float(hours_raw), 2))) if pd.notna(hours_raw) else None
        ot_raw = row.get("overtime_hours")
        overtime_hours = Decimal(str(round(float(ot_raw), 2))) if pd.notna(ot_raw) else None
        late_flag = str(row["late_flag"]).strip().upper() if pd.notna(row.get("late_flag")) else None
        source = str(row["source"]).strip() if pd.notna(row.get("source")) else None
        dq_flag = str(row["data_quality_flag"]).strip() if pd.notna(row.get("data_quality_flag")) else None
        dept_id = str(row["department_id"]).strip() if pd.notna(row.get("department_id")) else None

        attendance.append({
            "attendance_id": att_id,
            "employee_id": emp_id,
            "employee_code": emp_id,
            "attendance_date": att_date,
            "date": att_date,
            "weekday": weekday,
            "status": status,
            "leave_type_code": leave_code,
            "check_in": check_in,
            "check_out": check_out,
            "hours_worked": hours_worked,
            "overtime_hours": overtime_hours,
            "late_flag": late_flag,
            "source": source,
            "data_quality_flag": dq_flag,
            "notes": dq_flag,
            "department_id": dept_id,
        })

    # 8. Payroll Items (Export as test fixture answer key)
    if export_payroll_fixture:
        os.makedirs(FIXTURES_DIR, exist_ok=True)
        fixture_path = os.path.join(FIXTURES_DIR, "payroll_items_expected.json")
        if not os.path.exists(fixture_path):
            df_pi = xl.parse("payroll_items")
            pi_records = []
            for _, r in df_pi.iterrows():
                item_id = str(r.get("payroll_item_id") or r.get("item_id") or "").strip()
                run_id = str(r.get("run_id") or r.get("payroll_run_id") or "").strip()
                emp_id = str(r.get("employee_id") or "").strip()
                pi_records.append({
                    "payroll_item_id": item_id,
                    "run_id": run_id,
                    "employee_id": emp_id,
                    "period_start": str(parse_date_val(r.get("period_start"))),
                    "period_end": str(parse_date_val(r.get("period_end"))),
                    "gross_pay": float(r.get("gross_pay", 0.0) or 0.0),
                    "total_deductions": float(r.get("total_deductions", 0.0) or 0.0),
                    "net_pay": float(r.get("net_pay", 0.0) or 0.0),
                })
            with open(fixture_path, "w", encoding="utf-8") as f:
                json.dump(pi_records, f)

    return {
        "departments": departments,
        "roles": roles,
        "employees": employees,
        "salary_revisions": salary_revisions,
        "assignments": assignments,
        "salary_structures": salary_structures,
        "attendance": attendance,
    }


if __name__ == "__main__":
    print("Loading and cleaning master dataset from workbook...")
    dataset = load_and_clean_master_dataset()
    print("\nMaster dataset loaded and cleaned successfully:")
    for key, items in dataset.items():
        print(f"  {key:<22}: {len(items):>7} records")

