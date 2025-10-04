# backend/app.py
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from models import init_db, SessionLocal, Candidate
from seed import load_and_seed
from utils import parse_salary, extract_experience_years, compute_score, generate_reason, select_diverse
import json, os

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])
init_db()

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "form-submissions.json")

# Seed database once at startup (Flask 3.x compatible)
with app.app_context():
    try:
        session = SessionLocal()
        count = session.query(Candidate).count()
        session.close()
        if count == 0:
            print("No candidates found. Seeding database...")
            load_and_seed()
    except Exception as e:
        print("Seed error:", e)

@app.route("/api/candidates", methods=["GET"])
def list_candidates():
    q = request.args.get("q")
    min_exp = request.args.get("min_experience", type=float)
    max_salary = request.args.get("max_salary", type=int)
    sort_by = request.args.get("sort_by", "score")
    session = SessionLocal()
    query = session.query(Candidate)
    if q:
        # naive substring search in name and skills_raw
        like = "%{}%".format(q.lower())
        query = query.filter((Candidate.name.ilike(like)) | (Candidate.skills_raw.ilike(like)))
    if min_exp is not None:
        query = query.filter(Candidate.experience_years >= min_exp)
    if max_salary is not None:
        query = query.filter(Candidate.salary_expectation <= max_salary)
    if sort_by == "score":
        query = query.order_by(Candidate.score.desc())
    rows = query.all()
    out = []
    for r in rows:
        out.append({
            "id": r.id,
            "name": r.name,
            "email": r.email,
            "phone": r.phone,
            "location": r.location,
            "submitted_at": str(r.submitted_at),
            "availability": json.loads(r.availability or "[]"),
            "salary_expectation": r.salary_expectation,
            "work_experiences": json.loads(r.work_experience_raw or "[]"),
            "education": json.loads(r.education_raw or "{}"),
            "skills": json.loads(r.skills_raw or "[]"),
            "experience_years": r.experience_years,
            "score": r.score,
            "selected": r.selected,
            "reason": r.reason
        })
    session.close()
    return jsonify({"candidates": out})

@app.route("/api/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error":"no file"}), 400
    f = request.files['file']
    if not f.filename.endswith(".json"):
        return jsonify({"error":"only json"}), 400
    data = json.load(f)
    # write to data path
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    # re-seed
    load_and_seed()
    return jsonify({"status":"ok","count": len(data)})

@app.route("/api/select/<int:candidate_id>", methods=["POST"])
def select_candidate(candidate_id):
    session = SessionLocal()
    r = session.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not r:
        session.close()
        return jsonify({"error":"not found"}), 404
    # mark selected and write reason
    # build candidate dict
    cand_dict = {
        "skills": json.loads(r.skills_raw or "[]"),
        "experience_years": r.experience_years,
        "education": json.loads(r.education_raw or "{}"),
        "availability": json.loads(r.availability or "[]"),
        "salary_expectation": r.salary_expectation
    }
    r.selected = True
    r.reason = generate_reason(cand_dict)
    session.commit()
    session.close()
    return jsonify({"status":"ok","id": candidate_id})

@app.route("/api/auto_select", methods=["POST"])
def auto_select():
    session = SessionLocal()
    rows = session.query(Candidate).all()
    cand_list = []
    for r in rows:
        cand_list.append({
            "id": r.id,
            "name": r.name,
            "skills": json.loads(r.skills_raw or "[]"),
            "experience_years": r.experience_years,
            "education": json.loads(r.education_raw or "{}"),
            "availability": json.loads(r.availability or "[]"),
            "salary_expectation": r.salary_expectation,
            "score": r.score
        })
    chosen = select_diverse(cand_list, k=5)
    # reset
    for r in rows:
        r.selected = False
        r.reason = None
    session.commit()
    for c in chosen:
        row = session.query(Candidate).filter(Candidate.id == c["id"]).first()
        if row:
            row.selected = True
            row.reason = generate_reason(c)
    session.commit()
    session.close()
    return jsonify({"status":"ok", "selected":[{"id":c["id"],"name":c["name"], "score":c["score"]} for c in chosen]})

@app.route("/api/selected", methods=["GET"])
def get_selected():
    session = SessionLocal()
    rows = session.query(Candidate).filter(Candidate.selected == True).all()
    out = []
    for r in rows:
        out.append({"id":r.id, "name":r.name, "location":r.location, "skills": json.loads(r.skills_raw or "[]"), "score": r.score, "reason": r.reason})
    session.close()
    return jsonify({"selected": out})

if __name__ == "__main__":
    # run dev server
    app.run(host="0.0.0.0", port=8000, debug=True)