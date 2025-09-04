from typing import List, Dict

JOBS: List[Dict] = [
    {"title":"Software Engineer (Flask)","skills":["python","flask","sql"],"company":"TechCorp","location":"Remote","type":"Private"},
    {"title":"Data Analyst","skills":["excel","sql","python","power bi"],"company":"DataWorld","location":"Noida","type":"Private"},
    {"title":"AI Research Intern","skills":["machine learning","python","nlp"],"company":"AI Labs","location":"Bengaluru","type":"Private"},
    {"title":"Frontend Developer","skills":["javascript","react","html","css"],"company":"WebWorks","location":"Remote","type":"Private"},
    {"title":"Govt. Junior Data Entry","skills":["excel","typing","ms office"],"company":"Gov Dept","location":"Lucknow","type":"Government"},
    {"title":"International Support (US Shift)","skills":["english","communication","customer support"],"company":"GlobalHelp Inc","location":"Remote","type":"International"},
]

def match_jobs(skills: List[str]):
    matches = []
    sset = set(skills)
    for job in JOBS:
        jset = set(job["skills"])
        overlap = sorted(list(sset & jset))
        if overlap:
            score = round(100 * len(overlap) / max(1, len(jset)))
            matches.append({
                **job,
                "matched_skills": overlap,
                "score": score
            })
    return sorted(matches, key=lambda x: x["score"], reverse=True)
