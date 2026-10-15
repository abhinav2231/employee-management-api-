import logging
import os
import sys
from typing import Optional, Dict, Any
import pandas as pd
from sqlalchemy.orm import Session, joinedload

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, engine

engine.echo = False
from app.models.employee import Employee
from app.models.role import Role
from app.models.department import Department
from app.models.salary_structure import SalaryStructure
from app.models.attendance import Attendance
from app.models.salary_revision import SalaryRevision
from app.models.assignment import EmployeeAssignment

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORTS_DIR = os.path.join(REPO_ROOT, "exports")
DATA_EXPORTS_DIR = os.path.join(REPO_ROOT, "data", "exports")


def export_database_to_csv(output_dir: str = EXPORTS_DIR, db: Optional[Session] = None) -> Dict[str, Any]:
    """Exports master tables from the database to clean standardized CSV files."""
    os.makedirs(output_dir, exist_ok=True)
    # Also ensure data/exports directory exists
    os.makedirs(DATA_EXPORTS_DIR, exist_ok=True)

    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        # 1. Employees Export
        employees = (
            db.query(Employee)
            .options(
                joinedload(Employee.department),
                joinedload(Employee.role),
                joinedload(Employee.manager),
            )
            .order_by(Employee.employee_id.asc())
            .all()
        )
        emp_rows = []
        for e in employees:
            role_title = e.role.role_title if e.role else None
            emp_rows.append({
                "employee_id": e.employee_id,
                "employee_code": e.employee_id,
                "first_name": e.first_name,
                "last_name": e.last_name,
                "full_name": e.full_name,
                "work_email": e.work_email,
                "email": e.work_email,
                "phone_number": e.phone_number,
                "gender": e.gender,
                "date_of_birth": e.date_of_birth,
                "department_id": e.department_id,
                "department_name": e.department.department_name if e.department else None,
                "role_id": e.role_id,
                "role_title": role_title,
                "manager_id": e.manager_id,
                "salary": e.salary,
                "hire_date": e.hire_date,
                "exit_date": e.exit_date,
                "employment_status": e.employment_status,
                "employment_type": e.employment_type,
                "exit_type": e.exit_type,
                "exit_reason": e.exit_reason,
                "work_location": e.work_location,
                "work_mode": e.work_mode,
                "highest_education": e.highest_education,
                "prior_experience_years": e.prior_experience_years,
                "career_gap_months": e.career_gap_months,
                "commute_distance_km": e.commute_distance_km,
                "pf_applicable": e.pf_applicable,
                "esi_applicable": e.esi_applicable,
                "notice_period_days": e.notice_period_days,
                "resignation_date": e.resignation_date,
                "is_active": e.is_active,
            })
        df_emp = pd.DataFrame(emp_rows)
        emp_csv = os.path.join(output_dir, "employees.csv")
        df_emp.to_csv(emp_csv, index=False)
        df_emp.to_csv(os.path.join(DATA_EXPORTS_DIR, "employees.csv"), index=False)

        # 2. Salary Structures Export
        structures = (
            db.query(SalaryStructure)
            .order_by(SalaryStructure.employee_id.asc(), SalaryStructure.effective_from.asc())
            .all()
        )
        struct_rows = []
        for s in structures:
            struct_rows.append({
                "structure_id": s.structure_id,
                "employee_id": s.employee_id,
                "component_id": s.component_id,
                "component_name": s.component_name,
                "component_type": s.component_type,
                "monthly_amount": s.monthly_amount,
                "effective_from": s.effective_from,
                "effective_to": s.effective_to,
                "revision_id": s.revision_id,
            })
        df_struct = pd.DataFrame(struct_rows)
        struct_csv = os.path.join(output_dir, "salary_structures.csv")
        df_struct.to_csv(struct_csv, index=False)
        df_struct.to_csv(os.path.join(DATA_EXPORTS_DIR, "salary_structures.csv"), index=False)

        # 3. Attendance Export
        att_rows = []
        attendances = (
            db.query(Attendance)
            .order_by(Attendance.attendance_date.asc(), Attendance.employee_id.asc())
            .all()
        )
        for a in attendances:
            att_rows.append({
                "attendance_id": a.attendance_id,
                "employee_id": a.employee_id,
                "attendance_date": a.attendance_date,
                "weekday": a.weekday,
                "status": a.status,
                "leave_type_code": a.leave_type_code,
                "check_in": a.check_in,
                "check_out": a.check_out,
                "hours_worked": a.hours_worked,
                "overtime_hours": a.overtime_hours,
                "late_flag": a.late_flag,
                "source": a.source,
                "data_quality_flag": a.data_quality_flag,
                "department_id": a.department_id,
            })
        df_att = pd.DataFrame(att_rows)
        att_csv = os.path.join(output_dir, "attendance.csv")
        df_att.to_csv(att_csv, index=False)
        df_att.to_csv(os.path.join(DATA_EXPORTS_DIR, "attendance.csv"), index=False)

        # 4. Salary Revisions Export
        revisions = (
            db.query(SalaryRevision)
            .order_by(SalaryRevision.employee_id.asc(), SalaryRevision.effective_from.asc())
            .all()
        )
        rev_rows = []
        for r in revisions:
            rev_rows.append({
                "revision_id": r.revision_id,
                "employee_id": r.employee_id,
                "effective_from": r.effective_from,
                "revision_reason": r.revision_reason,
                "previous_annual_fixed": r.previous_annual_fixed,
                "new_annual_fixed": r.new_annual_fixed,
                "pct_change": r.pct_change,
                "role_id_after": r.role_id_after,
                "approved_by": r.approved_by,
            })
        df_rev = pd.DataFrame(rev_rows)
        rev_csv = os.path.join(output_dir, "salary_revisions.csv")
        df_rev.to_csv(rev_csv, index=False)
        df_rev.to_csv(os.path.join(DATA_EXPORTS_DIR, "salary_revisions.csv"), index=False)

        # 5. Assignments Export
        assignments = (
            db.query(EmployeeAssignment)
            .order_by(EmployeeAssignment.employee_id.asc(), EmployeeAssignment.effective_from.asc())
            .all()
        )
        asg_rows = []
        for asg in assignments:
            asg_rows.append({
                "assignment_id": asg.assignment_id,
                "employee_id": asg.employee_id,
                "effective_from": asg.effective_from,
                "effective_to": asg.effective_to,
                "department_id": asg.department_id,
                "role_id": asg.role_id,
                "job_level": asg.job_level,
                "manager_id": asg.manager_id,
                "change_reason": asg.change_reason,
            })
        df_asg = pd.DataFrame(asg_rows)
        asg_csv = os.path.join(output_dir, "assignments.csv")
        df_asg.to_csv(asg_csv, index=False)
        df_asg.to_csv(os.path.join(DATA_EXPORTS_DIR, "assignments.csv"), index=False)

        return {
            "employees_csv": emp_csv,
            "employees_count": len(emp_rows),
            "salary_structures_csv": struct_csv,
            "salary_structures_count": len(struct_rows),
            "attendance_csv": att_csv,
            "attendance_count": len(att_rows),
            "salary_revisions_csv": rev_csv,
            "salary_revisions_count": len(rev_rows),
            "assignments_csv": asg_csv,
            "assignments_count": len(asg_rows),
        }

    finally:
        if close_session:
            db.close()


if __name__ == "__main__":
    res = export_database_to_csv()
    print("CSV exports generated successfully:")
    for k, v in res.items():
        print(f"  {k}: {v}")
