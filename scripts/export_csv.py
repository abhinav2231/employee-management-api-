import logging
import os
import sys
from typing import Optional, Dict, Any
import pandas as pd
from sqlalchemy.orm import Session

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, engine

engine.echo = False
from app.models.employee import Employee
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
        employees = db.query(Employee).order_by(Employee.employee_code.asc()).all()
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
                "employment_type": e.employment_type,
                "is_active": e.is_active,
            })

        emp_df = pd.DataFrame(emp_rows)
        emp_path = os.path.join(output_dir, "employees.csv")
        emp_df.to_csv(emp_path, index=False, encoding="utf-8", lineterminator="\n")

        salaries = db.query(SalaryRecord).join(SalaryRecord.employee).order_by(Employee.employee_code.asc(), SalaryRecord.pay_period.asc()).all()
        sal_rows = []
        for s in salaries:
            sal_rows.append({
                "employee_code": s.employee.employee_code if s.employee else None,
                "employee_name": f"{s.employee.first_name} {s.employee.last_name}" if s.employee else None,
                "pay_period": s.pay_period,
                "effective_date": s.effective_date.isoformat() if s.effective_date else None,
                "base_salary": float(s.base_salary),
                "allowances": float(s.allowances),
                "bonuses": float(s.bonuses),
                "deductions": float(s.deductions),
                "net_salary": float(s.net_salary),
                "currency": s.currency,
                "payment_status": s.payment_status,
            })

        sal_df = pd.DataFrame(sal_rows)
        sal_path = os.path.join(output_dir, "salaries.csv")
        sal_df.to_csv(sal_path, index=False, encoding="utf-8", lineterminator="\n")

        attendance = db.query(Attendance).join(Attendance.employee).order_by(Employee.employee_code.asc(), Attendance.date.asc()).all()
        att_rows = []
        for a in attendance:
            att_rows.append({
                "employee_code": a.employee.employee_code if a.employee else None,
                "date": a.date.isoformat() if a.date else None,
                "status": a.status,
                "check_in": a.check_in.strftime("%H:%M:%S") if a.check_in else None,
                "check_out": a.check_out.strftime("%H:%M:%S") if a.check_out else None,
                "hours_worked": float(a.hours_worked) if a.hours_worked is not None else None,
                "notes": a.notes,
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
