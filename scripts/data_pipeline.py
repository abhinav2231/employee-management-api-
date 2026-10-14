from datetime import date, datetime, time
from decimal import Decimal
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

MASTER_DATASET_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "01_LedgerForge_Python_Master_Dataset.xlsx",
)


def parse_time_str(val: Any) -> Optional[time]:
    if val is None or pd.isna(val):
        return None
    if isinstance(val, time):
        return val
    if isinstance(val, datetime):
        return val.time()
    try:
        s = str(val).strip()
        parts = s.split(":")
        if len(parts) >= 2:
            return time(int(parts[0]), int(parts[1]))
    except Exception:
        pass
    return None


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


def load_and_clean_master_dataset(recent_attendance_months: int = 4) -> Dict[str, Any]:
    if not os.path.exists(MASTER_DATASET_PATH):
        raise FileNotFoundError(f"Master dataset file not found at: {MASTER_DATASET_PATH}")

    fake.seed_instance(RANDOM_SEED)
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    xl = pd.ExcelFile(MASTER_DATASET_PATH)

    df_depts = xl.parse("departments")
    departments = []
    for _, row in df_depts.iterrows():
        departments.append({
            "code": str(row["department_id"]).strip(),
            "name": str(row["department_name"]).strip(),
            "cost_center": str(row["cost_center"]).strip() if pd.notna(row.get("cost_center")) else None,
            "description": str(row["description"]).strip() if pd.notna(row.get("description")) else None,
            "is_active": True,
        })

    df_roles = xl.parse("roles")
    roles = []
    for _, row in df_roles.iterrows():
        roles.append({
            "code": str(row["role_id"]).strip(),
            "department_code": str(row["department_id"]).strip() if pd.notna(row.get("department_id")) else None,
            "title": str(row["role_title"]).strip(),
            "level": str(row["level"]).strip() if pd.notna(row.get("level")) else "L2",
            "is_active": True,
        })

    df_sal_rev = xl.parse("salary_revisions")
    df_sal_sorted = df_sal_rev.sort_values("effective_from")
    latest_salary_map: Dict[str, Decimal] = {}
    for _, row in df_sal_sorted.iterrows():
        emp_id = str(row["employee_id"]).strip()
        val = row.get("new_annual_fixed")
        if pd.notna(val) and float(val) > 0:
            latest_salary_map[emp_id] = Decimal(str(int(val)))

    df_emp = xl.parse("employees")
    employees = []
    used_emails = set()

    for idx, row in df_emp.iterrows():
        emp_code = str(row["employee_id"]).strip()
        first_name = str(row["first_name"]).strip()
        last_name = str(row["last_name"]).strip()

        base_email = f"{first_name.lower()}.{last_name.lower()}@auraworkforce.io"
        if base_email in used_emails:
            clean_code = emp_code.lower().replace("-", "")
            email = f"{first_name.lower()}.{last_name.lower()}.{clean_code}@auraworkforce.io"
        else:
            email = base_email
        used_emails.add(email)

        phone_number = fake.phone_number()
        hire_date = parse_date_val(row.get("hire_date"))
        exit_date = parse_date_val(row.get("exit_date"))
        dob = parse_date_val(row.get("date_of_birth"))
        status_str = str(row.get("employment_status", "Active")).strip()
        is_active = (status_str.lower() == "active")
        exit_type = str(row.get("exit_type")).strip() if pd.notna(row.get("exit_type")) else None
        exit_reason = str(row.get("exit_reason")).strip() if pd.notna(row.get("exit_reason")) else None
        work_mode = str(row.get("work_mode", "Hybrid")).strip() if pd.notna(row.get("work_mode")) else "Hybrid"
        pf_val = str(row.get("pf_applicable", "")).strip().upper()
        pf_applicable = True if pf_val in ["Y", "YES", "TRUE", "1"] else False if pf_val in ["N", "NO", "FALSE", "0"] else None
        esi_val = str(row.get("esi_applicable", "")).strip().upper()
        esi_applicable = True if esi_val in ["Y", "YES", "TRUE", "1"] else False if esi_val in ["N", "NO", "FALSE", "0"] else None

        salary = latest_salary_map.get(emp_code, Decimal("500000.00"))
        dept_code = str(row.get("department_id", "D01")).strip()
        role_code = str(row.get("role_id", "R002")).strip()
        manager_code = str(row["manager_id"]).strip() if pd.notna(row.get("manager_id")) else None

        employees.append({
            "employee_code": emp_code,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone_number": phone_number,
            "date_of_birth": dob,
            "department_code": dept_code,
            "role_code": role_code,
            "manager_code": manager_code,
            "salary": salary,
            "hire_date": hire_date or date(2022, 1, 1),
            "exit_date": exit_date,
            "employment_status": status_str,
            "exit_type": exit_type,
            "exit_reason": exit_reason,
            "work_mode": work_mode,
            "pf_applicable": pf_applicable,
            "esi_applicable": esi_applicable,
            "is_active": is_active,
            "work_location": str(row.get("work_location", "Bangalore")).strip(),
            "employment_type": str(row.get("employment_type", "Permanent")).strip(),
        })

    salary_revisions = []
    for _, row in df_sal_sorted.iterrows():
        rev_code = str(row["revision_id"]).strip()
        emp_code = str(row["employee_id"]).strip()
        eff_from = parse_date_val(row.get("effective_from"))
        reason = str(row["revision_reason"]).strip() if pd.notna(row.get("revision_reason")) else None
        prev_fixed = Decimal(str(int(row["previous_annual_fixed"]))) if pd.notna(row.get("previous_annual_fixed")) else None
        new_fixed_val = row.get("new_annual_fixed")
        new_fixed = Decimal(str(int(new_fixed_val))) if pd.notna(new_fixed_val) and float(new_fixed_val) > 0 else Decimal("0")
        pct = Decimal(str(round(float(row["pct_change"]), 2))) if pd.notna(row.get("pct_change")) else None
        role_after = str(row["role_id_after"]).strip() if pd.notna(row.get("role_id_after")) else None
        approved = str(row["approved_by"]).strip() if pd.notna(row.get("approved_by")) else None
        if eff_from and new_fixed > 0:
            salary_revisions.append({
                "revision_code": rev_code,
                "employee_code": emp_code,
                "effective_from": eff_from,
                "revision_reason": reason,
                "previous_annual_fixed": prev_fixed,
                "new_annual_fixed": new_fixed,
                "pct_change": pct,
                "role_id_after": role_after,
                "approved_by": approved,
            })

    df_asg = xl.parse("employee_assignments")
    assignments = []
    for _, row in df_asg.iterrows():
        asg_code = str(row["assignment_id"]).strip()
        emp_code = str(row["employee_id"]).strip()
        eff_from = parse_date_val(row.get("effective_from"))
        eff_to = parse_date_val(row.get("effective_to"))
        dept_code = str(row["department_id"]).strip() if pd.notna(row.get("department_id")) else None
        role_code = str(row["role_id"]).strip() if pd.notna(row.get("role_id")) else None
        lvl = int(row["job_level"]) if pd.notna(row.get("job_level")) else None
        mgr_code = str(row["manager_id"]).strip() if pd.notna(row.get("manager_id")) else None
        reason = str(row["change_reason"]).strip() if pd.notna(row.get("change_reason")) else None
        if eff_from:
            assignments.append({
                "assignment_code": asg_code,
                "employee_code": emp_code,
                "effective_from": eff_from,
                "effective_to": eff_to,
                "department_code": dept_code,
                "role_code": role_code,
                "job_level": lvl,
                "manager_code": mgr_code,
                "change_reason": reason,
            })

    df_pi = xl.parse("payroll_items")
    salaries = []
    min_pay_date = pd.to_datetime("2026-01-01")
    df_pi_filtered = df_pi[df_pi["period_start"] >= min_pay_date]
    if len(df_pi_filtered) == 0:
        df_pi_filtered = df_pi

    for _, row in df_pi_filtered.iterrows():
        emp_code = str(row["employee_id"]).strip()
        period_start = pd.to_datetime(row["period_start"])
        period_end = pd.to_datetime(row["period_end"])
        pay_period = period_start.strftime("%Y-%m")

        basic = float(row.get("basic", 0.0))
        allowances = float(
            row.get("hra", 0.0)
            + row.get("conveyance", 0.0)
            + row.get("medical", 0.0)
            + row.get("special_allowance", 0.0)
        )
        bonuses = float(row.get("variable_pay", 0.0) + row.get("overtime_pay", 0.0))
        deductions = float(row.get("total_deductions", 0.0))
        net_pay = float(row.get("net_pay", 0.0))

        salaries.append({
            "employee_code": emp_code,
            "pay_period": pay_period,
            "effective_date": period_end.date(),
            "base_salary": round(Decimal(str(basic)), 2),
            "allowances": round(Decimal(str(allowances)), 2),
            "bonuses": round(Decimal(str(bonuses)), 2),
            "deductions": round(Decimal(str(deductions)), 2),
            "net_salary": round(Decimal(str(net_pay)), 2),
            "currency": "INR",
            "payment_status": "PAID",
        })

    df_att = xl.parse("attendance")
    max_att_date = pd.to_datetime(df_att["attendance_date"]).max()
    min_att_date = max_att_date - pd.DateOffset(months=recent_attendance_months) if pd.notna(max_att_date) else pd.to_datetime("2026-06-01")
    df_att_recent = df_att[df_att["attendance_date"] >= min_att_date]
    if len(df_att_recent) == 0:
        df_att_recent = df_att.tail(20000)

    attendance = []
    for _, row in df_att_recent.iterrows():
        emp_code = str(row["employee_id"]).strip()
        att_date = pd.to_datetime(row["attendance_date"]).date()
        raw_status = str(row.get("status", "PRESENT")).strip().upper()
        raw_leave = row.get("leave_type_code")
        leave_code = None
        if pd.notna(raw_leave):
            clean_leave = str(raw_leave).strip().upper()
            if clean_leave and clean_leave not in ["NAN", "NONE"]:
                leave_code = clean_leave

        if raw_status == "ABSENT_LOP":
            status = "ABSENT_LOP"
        elif raw_status == "HALF_DAY_UNPAID":
            status = "HALF_DAY_UNPAID"
        elif raw_status == "UNPAID_LEAVE" or leave_code in ["LWP", "LOP"] or "UNPAID" in raw_status:
            status = "UNPAID_LEAVE"
        elif raw_status == "PAID_LEAVE" or (leave_code and "LEAVE" in raw_status):
            status = "PAID_LEAVE"
        elif raw_status in ["WFH", "REMOTE"]:
            status = "REMOTE"
        elif "HALF" in raw_status:
            status = "HALF_DAY"
        elif "ABSENT" in raw_status:
            status = "ABSENT"
        elif "PRESENT" in raw_status:
            status = "PRESENT"
        elif leave_code:
            status = "PAID_LEAVE"
        else:
            status = "PRESENT"

        check_in = parse_time_str(row.get("check_in"))
        check_out = parse_time_str(row.get("check_out"))
        hours_raw = row.get("hours_worked")
        hours_worked = Decimal(str(round(float(hours_raw), 2))) if pd.notna(hours_raw) else None

        notes = None
        if leave_code:
            notes = f"Leave Code: {leave_code}"
        elif status == "REMOTE":
            notes = "Work From Home"

        attendance.append({
            "employee_code": emp_code,
            "date": att_date,
            "status": status,
            "check_in": check_in,
            "check_out": check_out,
            "hours_worked": hours_worked,
            "notes": notes,
        })

    return {
        "departments": departments,
        "roles": roles,
        "employees": employees,
        "salaries": salaries,
        "attendance": attendance,
        "assignments": assignments,
        "salary_revisions": salary_revisions,
    }
