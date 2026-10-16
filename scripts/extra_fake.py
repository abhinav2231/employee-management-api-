"""Extra fake employees generator using Faker with seed 2026 for Aura Workforce OS."""

from datetime import date
from decimal import Decimal
import random
from typing import List, Dict, Any
from faker import Faker

EXTRA_SEED = 2026


def generate_extra_employees(
    count: int = 50,
    start_id: int = 746,
    existing_depts: List[str] = None,
    existing_roles: Dict[str, List[str]] = None,
    existing_managers: List[str] = None,
) -> List[Dict[str, Any]]:
    """Generates extra synthetic employee records with fixed random seed 2026."""
    fake = Faker("en_IN")
    Faker.seed(EXTRA_SEED)
    random.seed(EXTRA_SEED)

    depts = existing_depts or [f"D{i:02d}" for i in range(1, 11)]
    locations = ["Bengaluru", "Pune", "Hyderabad", "Chennai", "Delhi NCR", "Mumbai", "Coimbatore"]
    work_modes = ["Hybrid", "Onsite", "Remote"]
    educations = [
        "B.E. Computer Science",
        "B.Tech Information Technology",
        "M.Tech Software Engineering",
        "MBA Finance",
        "B.Com Accounting",
        "B.Sc Statistics",
        "MCA",
    ]

    employees = []
    for i in range(count):
        emp_num = start_id + i
        emp_id = f"EMP-{emp_num:04d}"

        gender = random.choice(["Male", "Female"])
        first_name = fake.first_name_male() if gender == "Male" else fake.first_name_female()
        last_name = fake.last_name()
        full_name = f"{first_name} {last_name}"
        email = f"{first_name.lower()}.{last_name.lower()}.{emp_num}@znova-demo.example"
        phone = "+91" + fake.random_element(["6", "7", "8", "9"]) + fake.numerify("#########")

        dept_id = random.choice(depts)
        if existing_roles and dept_id in existing_roles and existing_roles[dept_id]:
            role_id = random.choice(existing_roles[dept_id])
        else:
            role_id = "R002"

        mgr_id = random.choice(existing_managers) if existing_managers else "EMP-0002"

        hire_dt = fake.date_between_dates(
            date_start=date(2021, 1, 1),
            date_end=date(2026, 9, 15),
        )
        dob = fake.date_between_dates(
            date_start=date(1975, 1, 1),
            date_end=date(2001, 1, 1),
        )

        salary_amount = Decimal(str(random.randint(350, 2800) * 1000))

        employees.append({
            "employee_id": emp_id,
            "employee_code": emp_id,
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
            "work_email": email,
            "email": email,
            "phone_number": phone,
            "gender": gender,
            "date_of_birth": dob,
            "hire_date": hire_dt,
            "exit_date": None,
            "employment_status": "Active",
            "employment_type": "Permanent",
            "department_id": dept_id,
            "role_id": role_id,
            "manager_id": mgr_id,
            "work_location": random.choice(locations),
            "work_mode": random.choice(work_modes),
            "highest_education": random.choice(educations),
            "prior_experience_years": Decimal(str(round(random.uniform(0.5, 8.0), 1))),
            "career_gap_months": random.choice([0, 0, 0, 3, 6]),
            "commute_distance_km": Decimal(str(round(random.uniform(2.0, 35.0), 1))),
            "pf_applicable": "Y",
            "esi_applicable": "N",
            "notice_period_days": 30,
            "resignation_date": None,
            "exit_type": None,
            "exit_reason": None,
            "salary": salary_amount,
            "is_active": True,
        })

    return employees


if __name__ == "__main__":
    extras = generate_extra_employees(50)
    print(f"Generated {len(extras)} extra employees with Faker seed {EXTRA_SEED}")
    print(f"Sample: {extras[0]['employee_id']} - {extras[0]['full_name']} ({extras[0]['work_email']})")
