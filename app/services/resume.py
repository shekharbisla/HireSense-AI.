# app/services/resume.py
# Robust resume parsing: name (spaCy+heuristics), email, phones, skills, education snippets.
import re
from collections import Counter

# lazy spaCy load; if model not installed we fall back to heuristics
try:
    import spacy
    try:
        _NLP = spacy.load("en_core_web_sm")
    except Exception:
        # if model isn't present, set None (we'll still work with heuristics)
        _NLP = None
except Exception:
    _NLP = None

# try to reuse central skills catalog if available
try:
    from app.services.skills_catalog import CORE_SKILLS, ALIASES
except Exception:
    CORE_SKILLS = [
        "python", "flask", "django", "sql", "mysql", "postgresql", "mongodb",
        "excel", "power bi", "tableau", "pandas", "numpy",
        "javascript", "typescript", "react", "next.js", "angular", "vue",
        "html", "css", "tailwind",
        "machine learning", "deep learning", "nlp", "pytorch", "tensorflow",
        "scikit-learn", "docker", "kubernetes", "aws", "gcp", "azure"
    ]
    ALIASES = {"py": "python", "python3": "python", "js": "javascript", "reactjs": "react",
               "nodejs": "node", "postgres": "postgresql", "powerbi": "power bi",
               "sklearn": "scikit-learn"}

_email_re = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+', re.I)
_phone_re = re.compile(r'(\+?\d[\d\-\s\(\)]{5,}\d)', re.I)  # flexible phone pattern

def _clean_line(l: str) -> str:
    return l.strip().strip(": ").strip()

# -------------------------
# Name extraction function
# -------------------------
def extract_name_from_text(text: str):
    """
    Robust name extraction:
      1) explicit label (Name: ...)
      2) spaCy PERSON NER (if NLP model available)
      3) fallback: first non-empty top line that is not email/phone/heading
    Returns None or string.
    """
    if not text:
        return None

    # 1) explicit labeled name patterns
    name_label_re = re.compile(r'^\s*(?:name|full name|candidate name)\s*[:\-]\s*(.+)$', re.I | re.M)
    m = name_label_re.search(text)
    if m:
        candidate = _clean_line(m.group(1))
        if candidate and len(candidate.split()) <= 6:
            return candidate

    # 2) spaCy NER (prefer most common PERSON entity)
    if _NLP:
        try:
            doc = _NLP(text)
            persons = [ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"]
            if persons:
                # filter out huge chunks, prefer shorter names
                persons = [p for p in persons if 1 <= len(p.split()) <= 6]
                if persons:
                    c = Counter(persons)
                    most_common = c.most_common(1)[0][0]
                    return most_common
        except Exception:
            pass

    # 3) fallback heuristics: top-most non-email/phone/heading line
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for i, l in enumerate(lines[:6]):  # only check first few lines
        ll = l.lower()
        if ll in ("resume", "cv") or 'curriculum' in ll:
            continue
        if _email_re.search(l) or _phone_re.search(l):
            continue
        # keep only letters, dots, hyphens and spaces
        candidate = re.sub(r'[^A-Za-z\s\.\-]', '', l).strip()
        if candidate and 1 <= len(candidate.split()) <= 6 and re.search(r'[A-Za-z]', candidate):
            return candidate

    return None

# -------------------------
# Email / phone extraction
# -------------------------
def extract_emails(text: str):
    return list({m.group(0).strip() for m in _email_re.finditer(text)})

def extract_phones(text: str):
    found = []
    for m in _phone_re.finditer(text):
        s = m.group(0).strip()
        digits = re.sub(r'\D', '', s)
        if len(digits) >= 6:
            found.append(re.sub(r'\s+', ' ', s))
    # preserve order + unique
    seen = set(); out = []
    for p in found:
        if p not in seen:
            seen.add(p); out.append(p)
    return out

# -------------------------
# Skills extraction
# -------------------------
_SKILL_NORM = {}
def _init_skill_index():
    if _SKILL_NORM:
        return
    for s in CORE_SKILLS:
        _SKILL_NORM[s.lower()] = s.lower()
    for a, target in ALIASES.items():
        _SKILL_NORM[a.lower()] = target.lower()
    extra = dict(_SKILL_NORM)
    for k, v in extra.items():
        _SKILL_NORM[k.replace('.', ' ')] = v

_init_skill_index()

def extract_skills(text: str):
    if not text:
        return []
    txt = text.lower()
    txt_norm = re.sub(r'[\(\)\[\],;/:@]|[\n\r]+', ' ', txt)
    matches = []
    seen = set()
    skills_by_len = sorted(set(_SKILL_NORM.keys()), key=lambda s: -len(s))
    for skill in skills_by_len:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, txt_norm):
            normalized = _SKILL_NORM[skill]
            if normalized not in seen:
                seen.add(normalized); matches.append(normalized)
    return matches

# -------------------------
# Main parser
# -------------------------
def parse_resume_structured(text: str):
    """
    Returns dict:
      name: str | None
      emails: []
      phones: []
      skills: []
      education_snippets: []
    """
    result = {
        "name": None,
        "emails": [],
        "phones": [],
        "skills": [],
        "education_snippets": []
    }
    if not text or not text.strip():
        return result

    result["emails"] = extract_emails(text)
    result["phones"] = extract_phones(text)
    result["skills"] = extract_skills(text)
    result["name"] = extract_name_from_text(text)

    # education snippet heuristics
    edu_re = re.compile(r'\b(bachelor|b\.?sc|btech|b\.?tech|m\.?sc|mtech|mba|degree|b\.?e|m\.?e)\b', re.I)
    edu_lines = []
    for ln in [l.strip() for l in text.splitlines() if l.strip()]:
        if edu_re.search(ln):
            edu_lines.append(ln)
    result["education_snippets"] = edu_lines[:6]
    return result

# quick manual test when running file directly
if __name__ == "__main__":
    sample = """Ravi Sharma
Email: ravi@example.com
Phone: +91 98765 43210
Skills: Python, Flask, SQL, React, Power BI, Machine Learning
Education: B. Tech CSE"""
    import json
    print(json.dumps(parse_resume_structured(sample), indent=2))
