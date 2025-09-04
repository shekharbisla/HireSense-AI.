from flask import Blueprint, request, jsonify, current_app
from ..services.resume import extract_skills, parse_resume_structured
from ..services.matcher import match_jobs

api_bp = Blueprint("api", __name__)

@api_bp.post("/match")
def api_match():
    data = request.get_json(silent=True) or {}
    resume = (data.get("resume") or "").strip()
    if not resume:
        return jsonify({"error": "resume text required"}), 400
    skills = extract_skills(resume)
    results = match_jobs(skills)
    current_app.logger.info("skills=%s, results=%d", skills, len(results))
    return jsonify({"skills": skills, "results": results}), 200

@api_bp.post("/parse")
def api_parse():
    data = request.get_json(silent=True) or {}
    resume = (data.get("resume") or "").strip()
    if not resume:
        return jsonify({"error": "resume text required"}), 400
    return jsonify(parse_resume_structured(resume)), 200
