# backend/utils.py
import re
import json
from dateutil import parser as dateparser
from datetime import datetime
from collections import Counter

# target skills for Mercor (customize)
TARGET_SKILLS = ["python","llms","prompt engineering","flask","fastapi","sql","docker","aws","gcp","airflow","annotation tooling","react","next.js","java","c++","ci/cd","mysql","postgres","kubernetes"]

def parse_salary(s):
    """Take strings like "$117,548" or "117548" or "USD 117,548" and return int USD or None"""
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return int(s)
    s = str(s)
    # remove currency symbols and commas
    s = s.replace(",", "")
    s = re.sub(r"[^0-9\.]", "", s)
    if s == "":
        return None
    try:
        return int(float(s))
    except:
        return None

def compute_years_from_range(start, end):
    try:
        sd = dateparser.parse(start)
        ed = dateparser.parse(end) if end else datetime.utcnow()
        delta = ed - sd
        return max(0.0, round(delta.days / 365.0, 2))
    except:
        return 0.0

def extract_experience_years(work_experiences):
    """
    work_experiences: list of dicts, each may have startDate, endDate fields.
    Heuristic:
      - If startDate/endDate available, use them to sum years.
      - Else fallback: count number of entries and assign 1 year each.
    """
    if not work_experiences:
        return 0.0
    total = 0.0
    counted = 0
    for e in work_experiences:
        start = e.get("startDate") or e.get("start") or e.get("from")
        end = e.get("endDate") or e.get("end") or e.get("to")
        if start:
            yrs = compute_years_from_range(start, end)
            if yrs > 0:
                total += yrs
                counted += 1
                continue
        # fallback: if roleName contains "X years" pattern
        desc = (e.get("roleName","") + " " + e.get("description","")).lower()
        m = re.search(r'(\d+(\.\d+)?)\s*(years|yrs|year)', desc)
        if m:
            total += float(m.group(1))
            counted += 1
        else:
            # fallback assume 1 year each if no dates
            total += 1.0
            counted += 1
    return round(total, 2)

def normalize_skill(s):
    return s.strip().lower()

def skill_match_score(candidate_skills):
    cand = [normalize_skill(s) for s in (candidate_skills or [])]
    cand_set = set(cand)
    matches = sum(1 for t in TARGET_SKILLS if t in cand_set)
    return matches / max(1, len(TARGET_SKILLS))

def education_score(education_obj):
    """education_obj might be dict with highest_level or degrees list"""
    if not education_obj:
        return 0.0
    hl = ""
    if isinstance(education_obj, dict):
        hl = (education_obj.get("highest_level") or "").lower()
    if "phd" in hl or "ph.d" in hl:
        return 1.0
    if "master" in hl or "m.s" in hl or "msc" in hl:
        return 0.8
    if "bachelor" in hl or "b.sc" in hl or "b.s" in hl or "b.tech" in hl or "b.e" in hl or "b.a" in hl:
        return 0.6
    return 0.4

def availability_score(availability):
    if not availability:
        return 0.5
    if isinstance(availability, list):
        a = ",".join(availability).lower()
    else:
        a = str(availability).lower()
    if "immediate" in a or "now" in a:
        return 1.0
    if "2 weeks" in a or "two weeks" in a:
        return 0.8
    if "1 month" in a or "month" in a:
        return 0.5
    return 0.6

def salary_norm_score(salary, smin, smax):
    if salary is None:
        return 0.5
    if smax == smin:
        return 0.5
    # lower salary is slightly preferred
    s = (smax - salary) / (smax - smin)
    return max(0.0, min(1.0, s))

def compute_score(candidate_dict, smin, smax):
    """
    Weights:
      skill: 40%
      experience: 20%
      education: 10%
      availability: 15%
      salary: 15%
    Returns 0-100
    """
    w = {"skill": 0.40, "experience": 0.20, "education": 0.10, "availability": 0.15, "salary": 0.15}
    sk = skill_match_score(candidate_dict.get("skills", []))
    exp = min(candidate_dict.get("experience_years", 0.0) / 10.0, 1.0)  # cap at 10 years
    edu = education_score(candidate_dict.get("education", {}))
    av = availability_score(candidate_dict.get("availability", ""))
    sal = salary_norm_score(candidate_dict.get("salary_expectation", None), smin, smax)
    score = sk*w["skill"] + exp*w["experience"] + edu*w["education"] + av*w["availability"] + sal*w["salary"]
    return round(score*100, 2)

def generate_reason(candidate_dict):
    parts = []
    skills = ", ".join(candidate_dict.get("skills", []))
    parts.append(f"Skills: {skills}")
    parts.append(f"Experience: {candidate_dict.get('experience_years', 0)} yrs")
    parts.append(f"Education: {candidate_dict.get('education', {}).get('highest_level','-')}")
    parts.append(f"Availability: {candidate_dict.get('availability','-')}")
    parts.append(f"Salary expectation: ${candidate_dict.get('salary_expectation','-')}")
    rec = []
    for s in (candidate_dict.get("skills", []) or []):
        low = s.lower()
        if "llm" in low or "prompt" in low:
            rec.append("LLM / eval fit")
        if "flask" in low or "fastapi" in low:
            rec.append("Backend strength")
        if "react" in low or "next.js" in low:
            rec.append("Frontend/product fit")
        if "payments" in low or "payments" in low:
            rec.append("Fintech/payments experience")
    if not rec:
        rec.append("Versatile candidate")
    return "; ".join(parts) + " — " + " | ".join(rec)

def select_diverse(candidates, k=5):
    """
    Simple greedy diversity-aware selection:
      - sort by score desc
      - pick top, then prefer candidates that add new skills (lower overlap)
    """
    chosen = []
    chosen_skills = []
    sorted_c = sorted(candidates, key=lambda x: x.get("score",0), reverse=True)
    for cand in sorted_c:
        if len(chosen) >= k: break
        sset = set([normalize_skill(skill) for skill in (cand.get("skills") or [])])
        if not chosen:
            chosen.append(cand); chosen_skills.append(sset); continue
        overlap = sum(len(sset & cs) for cs in chosen_skills)
        # prefer low overlap
        if overlap < 3 or len(chosen) < 2 or cand.get("score",0) > 85:
            chosen.append(cand); chosen_skills.append(sset)
    # fill if needed
    i=0
    while len(chosen) < k and i < len(sorted_c):
        if sorted_c[i] not in chosen:
            chosen.append(sorted_c[i])
        i+=1
    return chosen