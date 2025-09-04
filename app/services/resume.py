import re
from typing import List, Dict, Any
import phonenumbers

# ---------- spaCy setup (with graceful fallback) ----------
_NLP = None
_PHRASE_MATCHER = None

def _ensure_model():
    import spacy
    try:
        return spacy.load("en_core_web_sm")
    except Exception:
        try:
            from spacy.cli import download as spacy_download
            spacy_download("en_core_web_sm")
            return spacy.load("en_core_web_sm")
        except Exception:
            nlp = spacy.blank("en")
            if "sentencizer" not in nlp.pipe_names:
                nlp.add_pipe("sentencizer")
            return nlp

def _init_nlp():
    global _NLP, _PHRASE_MATCHER
    if _NLP is not None:
        return
    try:
        import spacy
        from spacy.matcher import PhraseMatcher
        from .skills_catalog import CORE_SKILLS, ALIASES

        _NLP = _ensure_model()
        _PHRASE_MATCHER = PhraseMatcher(_NLP.vocab, attr="LOWER")

        patterns = []
        for s in CORE_SKILLS: patterns.append(_NLP.make_doc(s))
        for a in ALIASES.keys(): patterns.append(_NLP.make_doc(a))
        _PHRASE_MATCHER.add("SKILLS", patterns)
    except Exception:
        _NLP = None
        _PHRASE_MATCHER = None

_init_nlp()

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
NAME_LINE_RE = re.compile(r"^[A-Za-z][A-Za-z .'-]{2,}$")

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def _lower(s: str) -> str:
    return _norm(s).lower()

def _aliases(s: str) -> str:
    try:
        from .skills_catalog import ALIASES
        t = s
        for alias, real in ALIASES.items():
            t = re.sub(rf"\b{re.escape(alias)}\b", real, t, flags=re.I)
        return t
    except Exception:
        return s

def extract_skills(resume_text: str) -> List[str]:
    from .skills_catalog import CORE_SKILLS
    txt = _aliases(_lower(resume_text))
    found = set()

    if _NLP is not None and _PHRASE_MATCHER is not None:
        doc = _NLP(txt)
        for _, i, j in _PHRASE_MATCHER(doc):
            span = doc[i:j].text.lower()
            if span in CORE_SKILLS:
                found.add(span)

    for s in CORE_SKILLS:
        if re.search(rf"\b{re.escape(s)}\b", txt, flags=re.I):
            found.add(s)

    return sorted(found)

def parse_resume_structured(resume_text: str) -> Dict[str, Any]:
    raw = _norm(resume_text)
    txt = _aliases(raw)
    lines = [l.strip() for l in txt.splitlines() if l.strip()]

    m = EMAIL_RE.search(txt)
    email = m.group(0) if m else None

    phones = []
    for match in phonenumbers.PhoneNumberMatcher(txt, "IN"):
        try:
            phones.append(phonenumbers.format_number(
                match.number, phonenumbers.PhoneNumberFormat.INTERNATIONAL))
        except Exception:
            pass
    phones = list(dict.fromkeys(phones))

    name = None
    for l in lines[:5]:
        if EMAIL_RE.search(l): continue
        if any(ch.isdigit() for ch in l): continue
        if len(l.split()) > 6: continue
        if NAME_LINE_RE.match(l):
            name = l.strip(" -•|"); break

    edu_lines = [l for l in lines if re.search(
        r"\b(b\.?tech|btech|be|b\.e\.|bsc|b\.sc|bca|mca|mtech|m\.?tech|mba|bba|phd|diploma|intermediate|12th|10th)\b",
        l, re.I)]

    skills = extract_skills(txt)

    return {
        "name": name,
        "email": email,
        "phones": phones,
        "skills": skills,
        "education_snippets": edu_lines[:5]
    }
