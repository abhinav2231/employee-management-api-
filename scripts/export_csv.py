import logging
import os
import sys
from typing import Optional, Dict, Any
import pandas as pd
from sqlalchemy.orm import Session, joinedload, selectinload

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, engine

engine.echo = False
from app.models.employee import Employee
from app.models.role import EmployeeRole
from app.models.salary import SalaryRecord
from app.models.attendance import Attendance

EXPORTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "exports",
)


def export_database_to_csv(output_dir: str = EXPORTS_DIR, db: Optional[Session] = None) -> Dict[str, Any]:
    os.makedirs(output_dir, exist_ok=True)
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        employees = (
            db.query(Employee)
            .options(
                joinedload(Employee.department),
                joinedload(Employee.manager),
                selectinload(Employee.employee_roles).joinedload(EmployeeRole.role),
            )
            .order_by(Employee.employee_code.asc())
            .all()
        )
        emp_rows = []
        for e in employees:
            primary_role = next((er.role.title for er in e.employee_roles if er.is_primary and er.role), None)
            emp_rows.append({
                "employee_code": e.employee_code,
                "first_name": e.first_name,
                "last_name": e.last_name,
                "email": e.email,
                "phone_number": e.phone_number,
                "department_code": e.department.code if e.department else None,
                "department_name": e.department.name if e.department else None,
                "role_title": primary_role,
                "manager_code": e.manager.employee_code if e.manager else None,
                "manager_name": f"{e.manager.first_name} {e.manager.last_name}" if e.manager else None,
                "salary": float(e.salary),
                "hire_date": e.hire_date.isoformat() if e.hire_date else None,
                "exit_date": e.exit_date.isoformat() if e.exit_date else None,
                "work_location": e.work_location,
                "work_mode": e.work_mode,
                "employment_type": e.employment_type,
                "employment_status": e.employment_status,
                "exit_type": e.exit_type,
                "exit_reason": e.exit_reason,
                "is_active": e.is_active,
            })

        emp_df = pd.DataFrame(emp_rows)
        emp_df["phone_number"] = emp_df["phone_number"].astype(str)
        emp_path = os.path.join(output_dir, "employees.csv")
        emp_df.to_csv(emp_path, index=False, encoding="utf-8", lineterminator="\n")

        sal_query = (
            db.query(
                Employee.employee_code,
                Employee.first_name,
                Employee.last_name,
                SalaryRecord.pay_period,
                SalaryRecord.effective_date,
                SalaryRecord.base_salary,
                SalaryRecord.allowances,
                SalaryRecord.bonuses,
                SalaryRecord.deductions,
                SalaryRecord.net_salary,
                SalaryRecord.currency,
                SalaryRecord.payment_status,
            )
            .join(Employee, SalaryRecord.employee_id == Employee.id)
            .order_by(Employee.employee_code.asc(), SalaryRecord.pay_period.asc())
            .all()
        )
        sal_rows = []
        for row in sal_query:
            sal_rows.append({
                "employee_code": row[0],
                "employee_name": f"{row[1]} {row[2]}",
                "pay_period": row[3],
                "effective_date": row[4].isoformat() if row[4] else None,
                "base_salary": float(row[5]),
                "allowances": float(row[6]),
                "bonuses": float(row[7]),
                "deductions": float(row[8]),
                "net_salary": float(row[9]),
                "currency": row[10],
                "payment_status": row[11],
            })

        sal_df = pd.DataFrame(sal_rows)
        sal_path = os.path.join(output_dir, "salaries.csv")
        sal_df.to_csv(sal_path, index=False, encoding="utf-8", lineterminator="\n")

        att_query = (
            db.query(
                Employee.employee_code,
                Attendance.date,
                Attendance.status,
                Attendance.check_in,
                Attendance.check_out,
                Attendance.hours_worked,
                Attendance.notes,
            )
            .join(Employee, Attendance.employee_id == Employee.id)
            .order_by(Employee.employee_code.asc(), Attendance.date.asc())
            .all()
        )
        att_rows = []
        for row in att_query:
            att_rows.append({
                "employee_code": row[0],
                "date": row[1].isoformat() if row[1] else None,
                "status": row[2],
                "check_in": row[3].strftime("%H:%M:%S") if row[3] else None,
                "check_out": row[4].strftime("%H:%M:%S") if row[4] else None,
                "hours_worked": float(row[5]) if row[5] is not None else None,
                "notes": row[6],
            })

        att_df = pd.DataFrame(att_rows)
        att_path = os.path.join(output_dir, "attendance.csv")
        att_df.to_csv(att_path, index=False, encoding="utf-8", lineterminator="\n")

        return {
            "employees_csv": emp_path,
            "salaries_csv": sal_path,
            "attendance_csv": att_path,
            "employees_count": len(emp_df),
            "salaries_count": len(sal_df),
            "attendance_count": len(att_df),
        }
    finally:
        if close_session:
            db.close()


if __name__ == "__main__":
    export_database_to_csv()
