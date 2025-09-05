# app/services/resume.py
# Robust resume parsing: name (spaCy+heuristics), email, phones, skills
import re
from collections import Counter

# Try to reuse spaCy if available; load lazily
try:
    import spacy
    _NLP = None
    # don't load model automatically to avoid slow boots in some envs;
    # attempt to load common small model if present
    try:
        _NLP = spacy.load("en_core_web_sm")
    except Exception:
        # model not installed or load failed — keep None and continue
        _NLP = None
except Exception:
    _NLP = None

# Import central skill catalog if present
try:
    from app.services.skills_catalog import CORE_SKILLS, ALIASES
except Exception:
    CORE_SKILLS = [
        "python", "flask", "django", "sql", "excel", "javascript", "react",
        "machine learning", "nlp", "pandas", "power bi", "tensorflow", "pytorch"
    ]
    ALIASES = {"py": "python", "js": "javascript", "sklearn": "scikit-learn", "powerbi": "power bi"}

_email_re = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+', re.I)
_phone_re = re.compile(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?)?[\d\-\s]{6,20}', re.I)

def _clean_line(l):
    return l.strip().strip(": ").strip()

def extract_name_from_text(text):
    """
    Robust name extraction:
      1) Label regex (Name: ...)
      2) spaCy NER PERSON (if available)
      3) Fallback: first non-empty line at top that doesn't look like email/phone/heading
    """
    if not text:
        return None

    # 1) explicit label "Name: ..."
    name_label_re = re.compile(r'^\s*(?:name|full name|candidate name)\s*[:\-]\s*(.+)$', re.I | re.M)
    m = name_label_re.search(text)
    if m:
        candidate = _clean_line(m.group(1))
        if candidate and 1 <= len(candidate.split()) <= 6:
            return candidate

    # 2) spaCy NER (prefer most common PERSON)
    if _NLP:
        try:
            doc = _NLP(text)
            persons = [ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"]
            if persons:
                persons = [p for p in persons if 1 <= len(p.split()) <= 6]
                if persons:
                    c = Counter(persons)
                    most_common = c.most_common(1)[0][0]
                    return most_common
        except Exception:
            pass

    # 3) heuristic fallback - top lines
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    email_re = _email_re
    phone_re = _phone_re
    for l in lines[:8]:
        ll = l.lower()
        if ll in ("resume", "cv") or 'curriculum' in ll:
            continue
        if email_re.search(l) or phone_re.search(l):
            continue
        # likely name: keep letters, dots, hyphens and spaces
        candidate = re.sub(r'[^A-Za-z\s\.\-]', '', l).strip()
        if candidate and 1 <= len(candidate.split()) <= 6 and re.search(r'[A-Za-z]', candidate):
            return candidate

    return None

def extract_emails(text):
    return list({m.group(0).strip() for m in _email_re.finditer(text)})

def extract_phones(text):
    found = []
    for m in _phone_re.finditer(text):
        s = m.group(0).strip()
        digits = re.sub(r'\D', '', s)
        if len(digits) >= 6:
            found.append(re.sub(r'\s+', ' ', s))
    # unique preserve order
    seen = set(); out = []
    for p in found:
        if p not in seen:
            seen.add(p); out.append(p)
    return out

# Build normalized skill index once
_SKILL_NORM = {}
def _init_skill_index():
    if _SKILL_NORM:
        return
    for s in CORE_SKILLS:
        _SKILL_NORM[s.lower()] = s.lower()
    for a, target in ALIASES.items():
        _SKILL_NORM[a.lower()] = target.lower()
    # add variants
    extra = dict(_SKILL_NORM)
    for k,v in extra.items():
        _SKILL_NORM[k.replace('.', ' ')] = v
_init_skill_index()

def extract_skills(text):
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

def parse_resume_structured(text):
    """
    Returns:
      {
        "name": str|None,
        "emails": [...],
        "phones": [...],
        "skills": [...],
        "education_snippets": [...]
      }
    """
    result = {"name": None, "emails": [], "phones": [], "skills": [], "education_snippets": []}
    if not text or not text.strip():
        return result

    result["emails"] = extract_emails(text)
    result["phones"] = extract_phones(text)
    result["skills"] = extract_skills(text)

    # name extraction (put at top)
    name = extract_name_from_text(text)
    result["name"] = name

    # education heuristics
    edu_re = re.compile(r'\b(bachelor|b\.?sc|btech|b\.?tech|m\.?sc|mtech|b\.?e|m\.?e|mba|degree)\b', re.I)
    edu_lines = [ln.strip() for ln in text.splitlines() if ln.strip() and edu_re.search(ln)]
    result["education_snippets"] = edu_lines[:5]

    return result

# Quick CLI test (optional)
if __name__ == "__main__":
    sample = """Ravi Sharma
Email: ravi@example.com
Phone: +91 98765 43210
Skills: Python, Flask, SQL, React
Education: B. Tech CSE"""
    print(parse_resume_structured(sample))
