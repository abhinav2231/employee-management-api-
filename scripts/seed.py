import argparse
import logging
import os
import sys
from typing import Any, Dict, List

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine
from app.models.department import Department
from app.models.role import Role, EmployeeRole
from app.models.employee import Employee
from app.models.attendance import Attendance
from app.models.salary import SalaryRecord
from scripts.data_pipeline import (
    load_and_clean_master_dataset,
    export_dataset_to_csv,
)

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


def seed_database(reset: bool = False) -> Dict[str, Any]:
    db: Session = SessionLocal()

    try:
        if reset:
            print("[INFO] Resetting database tables (--reset requested)...")
            db.execute(
                text(
                    "TRUNCATE TABLE attendance, salary_records, employee_assignments, "
                    "employee_roles, employees, roles, departments CASCADE;"
                )
            )
            db.commit()

        dataset = load_and_clean_master_dataset()
        depts_data = dataset["departments"]
        roles_data = dataset["roles"]
        raw_employees = dataset["employees"]
        raw_salaries = dataset["salaries"]
        raw_attendance = dataset["attendance"]

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
            d_id = dept_code_to_id.get(item["department_code"], 1)

            existing = existing_emp_by_code.get(code) or existing_emp_by_email.get(email)

            if existing:
                existing.first_name = item["first_name"]
                existing.last_name = item["last_name"]
                existing.department_id = d_id
                existing.salary = item["salary"]
                existing.phone_number = item["phone_number"]
                existing.work_location = item["work_location"]
                existing.employment_type = item["employment_type"]
                existing.hire_date = item["hire_date"]
                existing.exit_date = item["exit_date"]
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
                    department_id=d_id,
                    manager_id=None,
                    salary=item["salary"],
                    hire_date=item["hire_date"],
                    exit_date=item["exit_date"],
                    work_location=item["work_location"],
                    employment_type=item["employment_type"],
                    is_active=item["is_active"],
                )
                db.add(new_emp)
                db.flush()
                emp_code_to_id[code] = new_emp.id
                existing_emp_by_code[code] = new_emp
                inserted_emp_count += 1

        db.commit()

        existing_emp_roles = {
            (er.employee_id, er.role_id) for er in db.query(EmployeeRole).all()
        }

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
                if (emp_id, role_id) not in existing_emp_roles:
                    db.add(
                        EmployeeRole(
                            employee_id=emp_id,
                            role_id=role_id,
                            is_primary=True,
                        )
                    )
                    existing_emp_roles.add((emp_id, role_id))

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

        export_files = export_dataset_to_csv(dataset)

        return {
            "departments_total": len(dept_code_to_id),
            "roles_total": len(role_code_to_id),
            "employees_total": len(emp_code_to_id),
            "employees_inserted": inserted_emp_count,
            "employees_updated": updated_emp_count,
            "salaries_total": len(raw_salaries),
            "attendance_total": len(raw_attendance),
            "exports": export_files,
        }

    except Exception as exc:
        db.rollback()
        raise exc
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Aura Workforce OS Master Dataset Seeder")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Truncate all tables before seeding",
    )
    args = parser.parse_args()

    seed_database(reset=args.reset)


if __name__ == "__main__":
    main()
