# app/services/resume.py
# Robust resume parsing: name (spaCy+heuristics), email, phones, skills
import re
from collections import Counter

# Try to reuse spaCy if available; load lazily
try:
    import spacy
    _NLP = spacy.load("en_core_web_sm")
except Exception:
    _NLP = None

# If you have a central skills catalog, import it. Adjust path if needed.
# This expects app/services/skills_catalog.py to define CORE_SKILLS and ALIASES
try:
    from app.services.skills_catalog import CORE_SKILLS, ALIASES
except Exception:
    # fallback minimal catalog to avoid crashes if import fails
    CORE_SKILLS = [
        "python", "flask", "django", "sql", "excel", "javascript", "react",
        "machine learning", "nlp", "pandas", "power bi", "tensorflow", "pytorch"
    ]
    ALIASES = {"py": "python", "js": "javascript", "sklearn": "scikit-learn", "powerbi": "power bi"}


_email_re = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+', re.I)
_phone_re = re.compile(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?)?[\d\-\s]{6,15}', re.I)

def _clean_line(l):
    return l.strip().strip(": ").strip()

def extract_name_from_text(text):
    """
    Extract a person's name using:
      1) explicit labels "Name: ...".
      2) spaCy NER PERSON (if available).
      3) fallback: first non-empty top line not email/phone/heading.
    """
    if not text:
        return None

    # 1) label
    name_label_re = re.compile(r'^\s*(?:name|full name|candidate name)\s*[:\-]\s*(.+)$', re.I | re.M)
    m = name_label_re.search(text)
    if m:
        candidate = _clean_line(m.group(1))
        if candidate and len(candidate.split()) <= 6:
            return candidate

    # 2) spaCy NER
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

    # 3) fallback: top lines heuristic
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    email_re = _email_re
    phone_re = _phone_re
    for i, l in enumerate(lines[:6]):  # check only top few lines
        ll = l.lower()
        if ll in ("resume", "cv") or 'curriculum' in ll:
            continue
        if email_re.search(l) or phone_re.search(l):
            continue
        # likely name: reduce to only letters, dots, hyphens, spaces
        candidate = re.sub(r'[^A-Za-z\s\.\-]', '', l).strip()
        if candidate and 1 <= len(candidate.split()) <= 6 and re.search(r'[A-Za-z]', candidate):
            return candidate

    return None

def extract_emails(text):
    return list({m.group(0).strip() for m in _email_re.finditer(text)})  # unique

def extract_phones(text):
    found = []
    for m in _phone_re.finditer(text):
        s = m.group(0).strip()
        # basic validation: keep if contains at least 6 digits
        digits = re.sub(r'\D', '', s)
        if len(digits) >= 6:
            # normalize spacing/hyphens
            found.append(re.sub(r'\s+', ' ', s))
    # unique preserve order
    seen = set(); out = []
    for p in found:
        if p not in seen:
            seen.add(p); out.append(p)
    return out

# Build a normalized skill mapping for quick lookup
_SKILL_NORM = {}
def _init_skill_index():
    if _SKILL_NORM:
        return
    for s in CORE_SKILLS:
        _SKILL_NORM[s.lower()] = s.lower()
    for a, target in ALIASES.items():
        _SKILL_NORM[a.lower()] = target.lower()
    # add multi-word variants: strip punctuation
    extra = dict(_SKILL_NORM)
    for k,v in extra.items():
        _SKILL_NORM[k.replace('.', ' ')] = v
_init_skill_index()

def extract_skills(text):
    """
    Two-pass simple extractor:
      - Find direct phrase matches for multi-word skills first.
      - Then token scan for single word skills.
    Returns normalized list (lowercase) without duplicates, ordered by occurrence.
    """
    if not text:
        return []

    txt = text.lower()
    # normalize punctuation for matching
    txt_norm = re.sub(r'[\(\)\[\],;/:@]|[\n\r]+', ' ', txt)

    matches = []
    seen = set()

    # sort skills by descending length so multi-word get matched first
    skills_by_len = sorted(set(_SKILL_NORM.keys()), key=lambda s: -len(s))

    for skill in skills_by_len:
        # use word boundaries for single tokens, otherwise simple substring
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, txt_norm):
            normalized = _SKILL_NORM[skill]
            if normalized not in seen:
                seen.add(normalized); matches.append(normalized)

    # Return in order found (approx)
    return matches

def parse_resume_structured(text):
    """
    Main exported parser — returns a dict:
    {
      "name": str|None,
      "emails": [..],
      "phones": [..],
      "skills": [..],
      "education_snippets": [..]  # optional short lines containing degree keywords
    }
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

    # Extract emails and phones first
    result["emails"] = extract_emails(text)
    result["phones"] = extract_phones(text)

    # Extract skills
    result["skills"] = extract_skills(text)

    # Extract name (place at top — more likely correct)
    name = extract_name_from_text(text)
    result["name"] = name

    # Try to capture education lines (short heuristics)
    edu_re = re.compile(r'\b(bachelor|b\.?sc|btech|b\.?tech|m\.?sc|mtech|b\.?e|m\.?e|mba|degree)\b', re.I)
    edu_lines = []
    for l in [ln.strip() for ln in text.splitlines() if ln.strip()]:
        if edu_re.search(l):
            edu_lines.append(l)
    result["education_snippets"] = edu_lines[:5]

    return result

# If you want a tiny CLI quick-test (optional)
if __name__ == "__main__":  # quick self-test when run manually
    sample = """Ravi Sharma
Email: ravi@example.com
Phone: +91 98765 43210
Skills: Python, Flask, SQL, React, Power BI, Machine Learning
Education: B. Tech CSE"""
    print(parse_resume_structured(sample))
