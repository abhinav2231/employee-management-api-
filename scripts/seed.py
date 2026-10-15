import argparse
import logging
import os
import sys
from typing import Any, Dict, List, Optional
from decimal import Decimal

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text, insert
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine
from app.models.department import Department
from app.models.role import Role
from app.models.employee import Employee
from app.models.assignment import EmployeeAssignment
from app.models.attendance import Attendance
from app.models.salary_revision import SalaryRevision
from app.models.salary_structure import SalaryStructure
from scripts.data_pipeline import load_and_clean_master_dataset
from scripts.export_csv import export_database_to_csv, EXPORTS_DIR
from scripts.extra_fake import generate_extra_employees

engine.echo = False


def truncate_tables(db: Session) -> None:
    """Truncates all workforce tables in proper foreign key dependency order."""
    tables = [
        "attendance",
        "salary_structures",
        "salary_records",
        "salary_revisions",
        "employee_assignments",
        "employee_roles",
        "employees",
        "roles",
        "departments",
    ]
    for tbl in tables:
        try:
            db.execute(text(f"TRUNCATE TABLE {tbl} RESTART IDENTITY CASCADE;"))
            db.commit()
        except Exception:
            db.rollback()


def seed_departments(db: Session, depts_data: List[Dict[str, Any]]) -> Dict[str, str]:
    existing = {d.department_id: d for d in db.query(Department).all()}
    for d in depts_data:
        did = d["department_id"]
        if did in existing:
            dept = existing[did]
            dept.department_name = d["department_name"]
            dept.cost_center = d.get("cost_center")
            dept.description = d.get("description")
            dept.is_active = True
        else:
            db.add(
                Department(
                    department_id=did,
                    department_name=d["department_name"],
                    cost_center=d.get("cost_center"),
                    description=d.get("description"),
                    is_active=True,
                )
            )
    db.commit()
    return {d.department_id: d.department_id for d in db.query(Department).all()}


def seed_roles(db: Session, roles_data: List[Dict[str, Any]]) -> Dict[str, str]:
    existing = {r.role_id: r for r in db.query(Role).all()}
    for r in roles_data:
        rid = r["role_id"]
        if rid in existing:
            role = existing[rid]
            role.department_id = r.get("department_id")
            role.role_title = r["role_title"]
            role.level = r.get("level")
            role.grade = r.get("grade")
            role.band_min_annual = r.get("band_min_annual")
            role.band_mid_annual = r.get("band_mid_annual")
            role.band_max_annual = r.get("band_max_annual")
            role.overtime_eligible = r.get("overtime_eligible", "N")
            role.band_year = r.get("band_year", 2026)
            role.is_active = True
        else:
            db.add(
                Role(
                    role_id=rid,
                    department_id=r.get("department_id"),
                    role_title=r["role_title"],
                    level=r.get("level"),
                    grade=r.get("grade"),
                    band_min_annual=r.get("band_min_annual"),
                    band_mid_annual=r.get("band_mid_annual"),
                    band_max_annual=r.get("band_max_annual"),
                    overtime_eligible=r.get("overtime_eligible", "N"),
                    band_year=r.get("band_year", 2026),
                    is_active=True,
                )
            )
    db.commit()
    return {r.role_id: r.role_id for r in db.query(Role).all()}


def seed_employees(db: Session, emp_data: List[Dict[str, Any]]) -> tuple:
    existing = {e.employee_id: e for e in db.query(Employee).all()}
    inserted_count = 0

    # Pass 1: Insert or update base records without manager links
    for e in emp_data:
        eid = e["employee_id"]
        if eid in existing:
            emp = existing[eid]
            for k in (
                "first_name", "last_name", "full_name", "work_email", "phone_number",
                "gender", "date_of_birth", "department_id", "role_id", "salary",
                "hire_date", "exit_date", "employment_status", "employment_type",
                "exit_type", "exit_reason", "work_location", "work_mode",
                "highest_education", "prior_experience_years", "career_gap_months",
                "commute_distance_km", "pf_applicable", "esi_applicable",
                "notice_period_days", "resignation_date", "is_active"
            ):
                if k in e:
                    setattr(emp, k, e[k])
        else:
            inserted_count += 1
            emp = Employee(
                employee_id=eid,
                first_name=e["first_name"],
                last_name=e["last_name"],
                full_name=e.get("full_name", f"{e['first_name']} {e['last_name']}"),
                work_email=e["work_email"],
                phone_number=e.get("phone_number"),
                gender=e.get("gender"),
                date_of_birth=e.get("date_of_birth"),
                department_id=e["department_id"],
                role_id=e["role_id"],
                manager_id=None,
                salary=e.get("salary"),
                hire_date=e["hire_date"],
                exit_date=e.get("exit_date"),
                employment_status=e.get("employment_status", "Active"),
                employment_type=e.get("employment_type", "Permanent"),
                exit_type=e.get("exit_type"),
                exit_reason=e.get("exit_reason"),
                work_location=e.get("work_location"),
                work_mode=e.get("work_mode"),
                highest_education=e.get("highest_education"),
                prior_experience_years=e.get("prior_experience_years"),
                career_gap_months=e.get("career_gap_months", 0),
                commute_distance_km=e.get("commute_distance_km"),
                pf_applicable=e.get("pf_applicable", "Y"),
                esi_applicable=e.get("esi_applicable", "N"),
                notice_period_days=e.get("notice_period_days", 30),
                resignation_date=e.get("resignation_date"),
                is_active=e.get("is_active", True),
            )
            db.add(emp)

    db.commit()

    # Pass 2: Connect managers now that all employees exist
    emp_map = {e.employee_id: e for e in db.query(Employee).all()}
    for e in emp_data:
        eid = e["employee_id"]
        mgr_id = e.get("manager_id")
        if mgr_id and mgr_id in emp_map and eid in emp_map:
            emp_map[eid].manager_id = mgr_id

    db.commit()
    return {eid: eid for eid in emp_map.keys()}, inserted_count


def seed_assignments(db: Session, asg_data: List[Dict[str, Any]]) -> int:
    existing_ids = set(r[0] for r in db.query(EmployeeAssignment.assignment_id).all())
    to_insert = []
    for a in asg_data:
        aid = a["assignment_id"]
        if aid not in existing_ids:
            to_insert.append({
                "assignment_id": aid,
                "employee_id": a["employee_id"],
                "effective_from": a["effective_from"],
                "effective_to": a.get("effective_to"),
                "department_id": a.get("department_id"),
                "role_id": a.get("role_id"),
                "job_level": a.get("job_level"),
                "manager_id": a.get("manager_id"),
                "change_reason": a.get("change_reason"),
            })
            existing_ids.add(aid)

    if to_insert:
        db.execute(insert(EmployeeAssignment), to_insert)
        db.commit()
    return len(existing_ids)


def seed_salary_revisions(db: Session, rev_data: List[Dict[str, Any]]) -> int:
    existing_ids = set(r[0] for r in db.query(SalaryRevision.revision_id).all())
    to_insert = []
    for r in rev_data:
        rid = r["revision_id"]
        if rid not in existing_ids:
            to_insert.append({
                "revision_id": rid,
                "employee_id": r["employee_id"],
                "effective_from": r["effective_from"],
                "revision_reason": r.get("revision_reason"),
                "previous_annual_fixed": r.get("previous_annual_fixed"),
                "new_annual_fixed": r["new_annual_fixed"],
                "pct_change": r.get("pct_change"),
                "role_id_after": r.get("role_id_after"),
                "approved_by": r.get("approved_by"),
            })
            existing_ids.add(rid)

    if to_insert:
        db.execute(insert(SalaryRevision), to_insert)
        db.commit()
    return len(existing_ids)


def seed_salary_structures(db: Session, struct_data: List[Dict[str, Any]]) -> int:
    existing_ids = set(r[0] for r in db.query(SalaryStructure.structure_id).all())
    to_insert = []
    for s in struct_data:
        sid = s["structure_id"]
        if sid not in existing_ids:
            to_insert.append({
                "structure_id": sid,
                "employee_id": s["employee_id"],
                "component_id": s["component_id"],
                "component_name": s["component_name"],
                "component_type": s["component_type"],
                "monthly_amount": s["monthly_amount"],
                "effective_from": s["effective_from"],
                "effective_to": s.get("effective_to"),
                "revision_id": s.get("revision_id"),
            })
            existing_ids.add(sid)

    if to_insert:
        # Batch in chunks of 5000
        for i in range(0, len(to_insert), 5000):
            db.execute(insert(SalaryStructure), to_insert[i:i + 5000])
            db.commit()
    return len(existing_ids)


def seed_attendance(db: Session, att_data: List[Dict[str, Any]]) -> int:
    existing_ids = set(r[0] for r in db.query(Attendance.attendance_id).all())
    to_insert = []
    for a in att_data:
        aid = a["attendance_id"]
        if aid not in existing_ids:
            to_insert.append({
                "attendance_id": aid,
                "employee_id": a["employee_id"],
                "attendance_date": a["attendance_date"],
                "weekday": a.get("weekday"),
                "status": a["status"],
                "leave_type_code": a.get("leave_type_code"),
                "check_in": a.get("check_in"),
                "check_out": a.get("check_out"),
                "hours_worked": a.get("hours_worked"),
                "overtime_hours": a.get("overtime_hours"),
                "late_flag": a.get("late_flag"),
                "source": a.get("source"),
                "data_quality_flag": a.get("data_quality_flag"),
                "department_id": a.get("department_id"),
            })
            existing_ids.add(aid)

    if to_insert:
        # Batch in chunks of 5000
        for i in range(0, len(to_insert), 5000):
            db.execute(insert(Attendance), to_insert[i:i + 5000])
            db.commit()
    return len(existing_ids)


def seed_database(
    reset: bool = False,
    do_export: bool = True,
    add_extra_50: bool = False,
    recent_attendance_months: Optional[int] = None,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        if reset:
            truncate_tables(db)

        data = load_and_clean_master_dataset(recent_attendance_months=recent_attendance_months)

        seed_departments(db, data["departments"])
        seed_roles(db, data["roles"])

        emp_list = list(data["employees"])
        if add_extra_50:
            existing_mgrs = [e["employee_id"] for e in emp_list if e.get("employment_status") == "Active"]
            extra_emps = generate_extra_employees(50, start_id=len(emp_list) + 1, existing_managers=existing_mgrs)
            emp_list.extend(extra_emps)

        _, emp_inserted = seed_employees(db, emp_list)
        asg_count = seed_assignments(db, data["assignments"])
        rev_count = seed_salary_revisions(db, data["salary_revisions"])
        struct_count = seed_salary_structures(db, data["salary_structures"])
        att_count = seed_attendance(db, data["attendance"])

        exports = {}
        if do_export:
            exports = export_database_to_csv(db=db)

        return {
            "employees_inserted": emp_inserted,
            "departments_total": db.query(Department).count(),
            "roles_total": db.query(Role).count(),
            "employees_total": db.query(Employee).count(),
            "assignments_total": asg_count,
            "salary_revisions_total": rev_count,
            "salary_structures_total": struct_count,
            "attendance_total": att_count,
            "exports": exports,
        }
    finally:
        if close_session:
            db.close()


def main():
    parser = argparse.ArgumentParser(description="LedgerForge / Aura Workforce OS Master Dataset Seeder")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["reset"],
        help="Optional positional 'reset' command per LedgerForge specification",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Truncate all tables before seeding",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt when resetting tables",
    )
    parser.add_argument(
        "--extra-50",
        action="store_true",
        help="Add 50 extra employees using Faker seed 2026",
    )
    args = parser.parse_args()
    do_reset = args.reset or (args.command == "reset")

    summary = seed_database(reset=do_reset, add_extra_50=args.extra_50)
    print("Master dataset seeded successfully:")
    print(f"  Departments:       {summary['departments_total']}")
    print(f"  Roles:             {summary['roles_total']}")
    print(f"  Employees:         {summary['employees_total']}")
    print(f"  Assignments:       {summary['assignments_total']}")
    print(f"  Salary Revisions:  {summary['salary_revisions_total']}")
    print(f"  Salary Structures: {summary['salary_structures_total']}")
    print(f"  Attendance:        {summary['attendance_total']}")
    if summary.get("exports"):
        print(f"  Exports generated in {EXPORTS_DIR}")


if __name__ == "__main__":
    main()
