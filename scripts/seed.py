import argparse
import logging
import os
import sys
from typing import Any, Dict, List, Optional

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine
from app.models.department import Department
from app.models.role import Role, EmployeeRole
from app.models.employee import Employee
from app.models.assignment import EmployeeAssignment
from app.models.attendance import Attendance
from app.models.salary import SalaryRecord
from app.models.salary_revision import SalaryRevision
from scripts.data_pipeline import load_and_clean_master_dataset
from scripts.export_csv import export_database_to_csv, EXPORTS_DIR

engine.echo = False


def seed_departments(db: Session, depts_data: List[Dict[str, Any]]) -> Dict[str, int]:
    dept_code_to_id: Dict[str, int] = {}
    existing_by_code = {d.code: d for d in db.query(Department).all()}
    existing_by_name = {d.name: d for d in db.query(Department).all()}

    for d in depts_data:
        code = d["code"]
        name = d["name"]
        if code in existing_by_code:
            dept = existing_by_code[code]
            dept.name = name
            dept.cost_center = d["cost_center"]
            dept.description = d["description"]
            dept_code_to_id[code] = dept.id
        elif name in existing_by_name:
            dept = existing_by_name[name]
            dept.code = code
            dept.cost_center = d["cost_center"]
            dept.description = d["description"]
            dept_code_to_id[code] = dept.id
            existing_by_code[code] = dept
        else:
            dept = Department(
                code=code,
                name=name,
                cost_center=d["cost_center"],
                description=d["description"],
                is_active=True,
            )
            db.add(dept)
            db.flush()
            dept_code_to_id[code] = dept.id
            existing_by_code[code] = dept
            existing_by_name[name] = dept

    db.commit()
    return dept_code_to_id


def seed_roles(
    db: Session, roles_data: List[Dict[str, Any]], dept_code_to_id: Dict[str, int]
) -> Dict[str, int]:
    role_code_to_id: Dict[str, int] = {}
    existing_by_code = {r.code: r for r in db.query(Role).all() if r.code}
    existing_by_title = {r.title: r for r in db.query(Role).all()}

    for r in roles_data:
        code = r["code"]
        title = r["title"]
        d_id = dept_code_to_id.get(r["department_code"])

        if code in existing_by_code:
            role = existing_by_code[code]
            role.title = title
            role.department_id = d_id
            role.level = r["level"]
            role_code_to_id[code] = role.id
        elif title in existing_by_title:
            role = existing_by_title[title]
            role.code = code
            role.department_id = d_id
            role.level = r["level"]
            role_code_to_id[code] = role.id
            existing_by_code[code] = role
        else:
            role = Role(
                code=code,
                title=title,
                department_id=d_id,
                level=r["level"],
                is_active=True,
            )
            db.add(role)
            db.flush()
            role_code_to_id[code] = role.id
            existing_by_code[code] = role
            existing_by_title[title] = role

    db.commit()
    return role_code_to_id


def seed_database(
    reset: bool = False,
    db: Optional[Session] = None,
    do_export: bool = True,
    export_dir: str = EXPORTS_DIR,
) -> Dict[str, Any]:
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        if reset:
            print("[INFO] Resetting database tables (--reset requested)...")
            db.execute(
                text(
                    "TRUNCATE TABLE attendance, salary_records, salary_revisions, "
                    "employee_assignments, employee_roles, employees, roles, departments CASCADE;"
                )
            )
            db.commit()

        dataset = load_and_clean_master_dataset()
        depts_data = dataset["departments"]
        roles_data = dataset["roles"]
        raw_employees = dataset["employees"]
        raw_salaries = dataset["salaries"]
        raw_attendance = dataset["attendance"]
        raw_assignments = dataset.get("assignments", [])
        raw_revisions = dataset.get("salary_revisions", [])

        dept_code_to_id = seed_departments(db, depts_data)
        role_code_to_id = seed_roles(db, roles_data, dept_code_to_id)

        existing_emp_by_code = {
            e.employee_code: e for e in db.query(Employee).all() if e.employee_code
        }
        existing_emp_by_email = {e.email: e for e in db.query(Employee).all()}

        emp_code_to_id: Dict[str, int] = {}
        inserted_emp_count = 0
        updated_emp_count = 0

        for item in raw_employees:
            code = item["employee_code"]
            email = item["email"]
            d_id = dept_code_to_id.get(item["department_code"])
            if not d_id:
                raise ValueError(f"Department code '{item['department_code']}' not found in departments")

            existing = existing_emp_by_code.get(code) or existing_emp_by_email.get(email)

            if existing:
                existing.first_name = item["first_name"]
                existing.last_name = item["last_name"]
                existing.department_id = d_id
                existing.salary = item["salary"]
                existing.phone_number = item["phone_number"]
                existing.date_of_birth = item.get("date_of_birth")
                existing.work_location = item["work_location"]
                existing.work_mode = item.get("work_mode")
                existing.employment_type = item["employment_type"]
                existing.employment_status = item.get("employment_status")
                existing.hire_date = item["hire_date"]
                existing.exit_date = item["exit_date"]
                existing.exit_type = item.get("exit_type")
                existing.exit_reason = item.get("exit_reason")
                existing.pf_applicable = item.get("pf_applicable")
                existing.esi_applicable = item.get("esi_applicable")
                existing.is_active = item["is_active"]
                emp_code_to_id[code] = existing.id
                updated_emp_count += 1
            else:
                new_emp = Employee(
                    employee_code=code,
                    first_name=item["first_name"],
                    last_name=item["last_name"],
                    email=email,
                    phone_number=item["phone_number"],
                    date_of_birth=item.get("date_of_birth"),
                    department_id=d_id,
                    manager_id=None,
                    salary=item["salary"],
                    hire_date=item["hire_date"],
                    exit_date=item["exit_date"],
                    exit_type=item.get("exit_type"),
                    exit_reason=item.get("exit_reason"),
                    work_location=item["work_location"],
                    work_mode=item.get("work_mode"),
                    employment_type=item["employment_type"],
                    employment_status=item.get("employment_status"),
                    pf_applicable=item.get("pf_applicable"),
                    esi_applicable=item.get("esi_applicable"),
                    is_active=item["is_active"],
                )
                db.add(new_emp)
                db.flush()
                emp_code_to_id[code] = new_emp.id
                existing_emp_by_code[code] = new_emp
                inserted_emp_count += 1

        db.commit()

        for item in raw_employees:
            emp_id = emp_code_to_id.get(item["employee_code"])
            mgr_code = item.get("manager_code")

            if emp_id and mgr_code:
                mgr_id = emp_code_to_id.get(mgr_code)
                if mgr_id and mgr_id != emp_id:
                    db.execute(
                        text("UPDATE employees SET manager_id = :mgr_id WHERE id = :emp_id"),
                        {"mgr_id": mgr_id, "emp_id": emp_id},
                    )

            role_code = item.get("role_code")
            role_id = role_code_to_id.get(role_code)
            if emp_id and role_id:
                existing_primary = (
                    db.query(EmployeeRole)
                    .filter(EmployeeRole.employee_id == emp_id, EmployeeRole.is_primary.is_(True))
                    .first()
                )
                if existing_primary:
                    existing_primary.role_id = role_id
                else:
                    db.add(
                        EmployeeRole(
                            employee_id=emp_id,
                            role_id=role_id,
                            is_primary=True,
                        )
                    )

        db.commit()

        existing_asgs = {
            a.assignment_code: a
            for a in db.query(EmployeeAssignment).all()
            if a.assignment_code
        }
        to_insert_asg: List[EmployeeAssignment] = []
        for asg in raw_assignments:
            code = asg["assignment_code"]
            emp_id = emp_code_to_id.get(asg["employee_code"])
            if not emp_id:
                continue
            d_id = dept_code_to_id.get(asg["department_code"])
            r_id = role_code_to_id.get(asg["role_code"])
            m_id = emp_code_to_id.get(asg["manager_code"])
            if code in existing_asgs:
                rec = existing_asgs[code]
                rec.employee_id = emp_id
                rec.effective_from = asg["effective_from"]
                rec.effective_to = asg["effective_to"]
                rec.department_id = d_id
                rec.role_id = r_id
                rec.job_level = asg["job_level"]
                rec.manager_id = m_id
                rec.change_reason = asg["change_reason"]
            else:
                to_insert_asg.append(
                    EmployeeAssignment(
                        assignment_code=code,
                        employee_id=emp_id,
                        effective_from=asg["effective_from"],
                        effective_to=asg["effective_to"],
                        department_id=d_id,
                        role_id=r_id,
                        job_level=asg["job_level"],
                        manager_id=m_id,
                        change_reason=asg["change_reason"],
                    )
                )

        if to_insert_asg:
            db.bulk_save_objects(to_insert_asg)
            db.commit()

        existing_revs = {
            r.revision_code: r
            for r in db.query(SalaryRevision).all()
            if r.revision_code
        }
        to_insert_rev: List[SalaryRevision] = []
        for rev in raw_revisions:
            code = rev["revision_code"]
            emp_id = emp_code_to_id.get(rev["employee_code"])
            if not emp_id:
                continue
            if code in existing_revs:
                rec = existing_revs[code]
                rec.employee_id = emp_id
                rec.effective_from = rev["effective_from"]
                rec.revision_reason = rev["revision_reason"]
                rec.previous_annual_fixed = rev["previous_annual_fixed"]
                rec.new_annual_fixed = rev["new_annual_fixed"]
                rec.pct_change = rev["pct_change"]
                rec.role_id_after = rev["role_id_after"]
                rec.approved_by = rev["approved_by"]
            else:
                to_insert_rev.append(
                    SalaryRevision(
                        revision_code=code,
                        employee_id=emp_id,
                        effective_from=rev["effective_from"],
                        revision_reason=rev["revision_reason"],
                        previous_annual_fixed=rev["previous_annual_fixed"],
                        new_annual_fixed=rev["new_annual_fixed"],
                        pct_change=rev["pct_change"],
                        role_id_after=rev["role_id_after"],
                        approved_by=rev["approved_by"],
                    )
                )

        if to_insert_rev:
            db.bulk_save_objects(to_insert_rev)
            db.commit()

        existing_salaries = {
            (s.employee_id, s.pay_period): s for s in db.query(SalaryRecord).all()
        }

        inserted_sal_count = 0
        updated_sal_count = 0

        for sal in raw_salaries:
            emp_id = emp_code_to_id.get(sal["employee_code"])
            if not emp_id:
                continue

            key = (emp_id, sal["pay_period"])
            if key in existing_salaries:
                rec = existing_salaries[key]
                rec.base_salary = sal["base_salary"]
                rec.allowances = sal["allowances"]
                rec.bonuses = sal["bonuses"]
                rec.deductions = sal["deductions"]
                rec.net_salary = sal["net_salary"]
                rec.payment_status = sal["payment_status"]
                updated_sal_count += 1
            else:
                rec = SalaryRecord(
                    employee_id=emp_id,
                    pay_period=sal["pay_period"],
                    effective_date=sal["effective_date"],
                    base_salary=sal["base_salary"],
                    allowances=sal["allowances"],
                    bonuses=sal["bonuses"],
                    deductions=sal["deductions"],
                    net_salary=sal["net_salary"],
                    currency=sal["currency"],
                    payment_status=sal["payment_status"],
                )
                db.add(rec)
                existing_salaries[key] = rec
                inserted_sal_count += 1

        db.commit()

        existing_att = {
            (a.employee_id, a.date)
            for a in db.query(Attendance.employee_id, Attendance.date).all()
        }

        inserted_att_count = 0
        to_insert_att: List[Attendance] = []

        for att in raw_attendance:
            emp_id = emp_code_to_id.get(att["employee_code"])
            if not emp_id:
                continue

            key = (emp_id, att["date"])
            if key not in existing_att:
                to_insert_att.append(
                    Attendance(
                        employee_id=emp_id,
                        date=att["date"],
                        status=att["status"],
                        check_in=att["check_in"],
                        check_out=att["check_out"],
                        hours_worked=att["hours_worked"],
                        notes=att["notes"],
                    )
                )
                existing_att.add(key)
                inserted_att_count += 1

                if len(to_insert_att) >= 5000:
                    db.bulk_save_objects(to_insert_att)
                    db.commit()
                    to_insert_att = []

        if to_insert_att:
            db.bulk_save_objects(to_insert_att)
            db.commit()

        export_files = {}
        if do_export:
            export_files = export_database_to_csv(output_dir=export_dir, db=db)

        return {
            "departments_total": len(dept_code_to_id),
            "roles_total": len(role_code_to_id),
            "employees_total": len(emp_code_to_id),
            "employees_inserted": inserted_emp_count,
            "employees_updated": updated_emp_count,
            "assignments_total": len(raw_assignments),
            "salary_revisions_total": len(raw_revisions),
            "salaries_total": len(raw_salaries),
            "attendance_total": len(raw_attendance),
            "exports": export_files,
        }

    except Exception as exc:
        db.rollback()
        raise exc
    finally:
        if close_session:
            db.close()


def main():
    parser = argparse.ArgumentParser(description="Aura Workforce OS Master Dataset Seeder")
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
    args = parser.parse_args()

    if args.reset and not args.force:
        if sys.stdin.isatty():
            confirm = input("Are you sure you want to truncate all tables? (y/N): ").strip().lower()
            if confirm != "y":
                print("[INFO] Seeding aborted by user.")
                sys.exit(0)
        else:
            sys.exit("[ERROR] Running --reset in a non-interactive environment (e.g. CI, piped stdin, Docker) requires the explicit --force flag.")

    summary = seed_database(reset=args.reset)
    print("Master dataset seeded successfully:")
    print(f"  Departments:      {summary['departments_total']}")
    print(f"  Roles:            {summary['roles_total']}")
    print(f"  Employees:        {summary['employees_total']} (inserted: {summary['employees_inserted']}, updated: {summary['employees_updated']})")
    print(f"  Assignments:      {summary['assignments_total']}")
    print(f"  Salary Revisions: {summary['salary_revisions_total']}")
    print(f"  Salaries:         {summary['salaries_total']}")
    print(f"  Attendance:       {summary['attendance_total']}")
    if summary.get("exports"):
        csv_count = sum(1 for k in summary["exports"] if k.endswith("_csv"))
        print(f"  Exports generated: {csv_count} files in {EXPORTS_DIR}")


if __name__ == "__main__":
    main()
