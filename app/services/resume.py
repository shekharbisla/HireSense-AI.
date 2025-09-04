import re

ALIASES = {
    "py": "python", "python3": "python",
    "ml": "machine learning", "ai": "machine learning",
    "js": "javascript", "reactjs": "react",
    "msoffice": "ms office", "ms-office": "ms office"
}

SKILL_KEYWORDS = {
    "python","flask","sql","excel","javascript","react","html","css",
    "machine learning","nlp","typing","ms office","english",
    "communication","customer support","pandas","power bi","django"
}

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()

def extract_skills(resume_text: str):
    t = _normalize(resume_text)
    for alias, real in ALIASES.items():
        t = t.replace(alias, real)
    found = {kw for kw in SKILL_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", t)}
    return sorted(found)
