# Add these imports at top of file (if not already)
import re
from collections import Counter

# If your project already loads spaCy model elsewhere, reuse it.
# Otherwise initialize lazily:
try:
    import spacy
    _NLP = spacy.load("en_core_web_sm")
except Exception:
    _NLP = None

def _clean_line(l):
    return l.strip().strip(": ").strip()

def extract_name_from_text(text):
    """
    Robust name extraction:
      1) Label regex (Name: ...)
      2) spaCy NER PERSON (if available)
      3) Fallback: first non-empty line that doesn't look like email/phone/heading
    Returns None or string.
    """
    if not text:
        return None

    # 1) explicit label
    name_label_re = re.compile(r'^\s*(?:name|full name|candidate name)\s*[:\-]\s*(.+)$', re.I | re.M)
    m = name_label_re.search(text)
    if m:
        candidate = _clean_line(m.group(1))
        if candidate and len(candidate.split()) <= 6:
            return candidate

    # 2) try spaCy NER (prefer longest PERSON entity)
    if _NLP:
        try:
            doc = _NLP(text)
            persons = [ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"]
            if persons:
                # choose most common or longest (heuristic)
                persons = [p for p in persons if len(p.split()) <= 6]  # avoid huge chunks
                if persons:
                    # prefer the earliest occurrence or longest name
                    # return the most frequent if duplicates exist
                    c = Counter(persons)
                    most_common = c.most_common(1)[0][0]
                    return most_common
        except Exception:
            pass

    # 3) fallback: first non-empty line before email/phone line
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    email_re = re.compile(r'[\w\.-]+@[\w\.-]+', re.I)
    phone_re = re.compile(r'(\+?\d[\d\-\s\(\)]{5,}\d)', re.I)

    # prefer first line that is not 'resume' or 'cv' or contains email/phone
    for i, l in enumerate(lines[:6]):  # only check top few lines
        ll = l.lower()
        if 'resume' in ll or 'curriculum' in ll or 'cv' == ll:
            continue
        if email_re.search(l) or phone_re.search(l):
            continue
        # probably name
        candidate = re.sub(r'[^A-Za-z\s\.\-]', '', l).strip()
        # sanity checks: not too long, contains letters
        if candidate and 1 <= len(candidate.split()) <= 6 and re.search(r'[A-Za-z]', candidate):
            # If candidate appears immediately followed by Email: in same line? handle above
            return candidate

    return None

# Example usage inside existing parse function:
def parse_resume_structured(text):
    # your existing parsing code...
    result = {}
    # existing extractions (email, phones, skills...) ...
    # then extract name robustly:
    name = extract_name_from_text(text)
    result['name'] = name
    return result
