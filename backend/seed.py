# backend/seed.py
import json, os
from datetime import datetime
from models import init_db, SessionLocal, Candidate
from utils import parse_salary, extract_experience_years, compute_score
from sqlalchemy.exc import IntegrityError

# Path to JSON data
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "form-submissions.json")

def load_and_seed():
    init_db()
    session = SessionLocal()
    
    # Clear existing candidates
    session.query(Candidate).delete()
    session.commit()

    # Load JSON data
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Precompute salaries for scoring normalization
    salaries = []
    parsed = []
    for d in data:
        salary_obj = d.get("annual_salary_expectation") or {}
        salary_raw = (
            salary_obj.get("full-time")
            or salary_obj.get("full_time")
            or (list(salary_obj.values())[0] if salary_obj else None)
        )
        salary = parse_salary(salary_raw)
        salaries.append(salary if salary is not None else 0)
        parsed.append((d, salary))

    smin = min(salaries) if salaries else 0
    smax = max(salaries) if salaries else 1

    # Insert candidates into DB
    for d, salary in parsed:
        # Parse submitted_at into datetime
        submitted_at_str = d.get("submitted_at")
        if submitted_at_str:
            try:
                submitted_at = datetime.fromisoformat(submitted_at_str.replace("Z", "+00:00"))
            except Exception:
                submitted_at = datetime.utcnow()
        else:
            submitted_at = datetime.utcnow()

        work_exps = d.get("work_experiences") or d.get("work_experience") or []
        education = d.get("education") or {}
        skills = d.get("skills") or []
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",") if s.strip()]
        experience_years = extract_experience_years(work_exps)

        cand = Candidate(
            name=d.get("name"),
            email=d.get("email"),
            phone=d.get("phone"),
            location=d.get("location"),
            submitted_at=submitted_at,
            availability=json.dumps(d.get("work_availability") or d.get("availability") or []),
            salary_expectation=salary,
            work_experience_raw=json.dumps(work_exps),
            education_raw=json.dumps(education),
            skills_raw=json.dumps(skills),
            experience_years=experience_years
        )
        session.add(cand)

    session.commit()

    # Compute scores
    rows = session.query(Candidate).all()
    salaries = [r.salary_expectation or 0 for r in rows]
    smin = min(salaries) if salaries else 0
    smax = max(salaries) if salaries else 1

    for r in rows:
        cand_dict = {
            "skills": json.loads(r.skills_raw or "[]"),
            "experience_years": r.experience_years,
            "education": json.loads(r.education_raw or "{}"),
            "availability": json.loads(r.availability or "[]"),
            "salary_expectation": r.salary_expectation
        }
        r.score = compute_score(cand_dict, smin, smax)

    session.commit()
    session.close()

    print(f"Seed complete: {len(rows)} candidates")

if __name__ == "__main__":
    load_and_seed()