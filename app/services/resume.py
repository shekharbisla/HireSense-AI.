import re
from typing import List, Dict, Any
import phonenumbers

# spaCy setup with graceful fallback
_NLP = None
_PHRASE_MATCHER = None

def _init_nlp():
    global _NLP, _PHRASE_MATCHER
    if _NLP is not None:
        return
    try:
        import spacy
        # Try full model; if not present, fall back to blank English
        try:
            _NLP = spacy.load("en_core_web_sm")
        except Exception:
            _NLP = spacy.blank("en")
            if "sentencizer" not in _NLP.pipe_names:
                _NLP.add_pipe("sentencizer")
        from spacy.matcher import PhraseMatcher
        from .skills_catalog import CORE_SKILLS, ALIASES
        _PHRASE_MATCHER = PhraseMatcher(_NLP.vocab, attr="LOWER")
        patterns = []
        for skill in CORE_SKILLS:
            patterns.append(_NLP.make_doc(skill))
        for alias in ALIASES.keys():
            patterns.append(_NLP.make_doc(alias))
        _PHRASE_MATCHER.add("SKILLS", patterns)
    except Exception:
        _NLP = None
        _PHRASE_MATCHER = None

_init_nlp()

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
NAME_LINE_RE = re.compile(r"^[A-Za-z][A-Za-z .'-]{2,}$")

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def _normalize_lower(text: str) -> str:
    return _normalize(text).lower()

def _apply_aliases(text: str) -> str:
    try:
        from .skills_catalog import ALIASES
        t = text
        for alias, real in ALIASES.items():
            t = re.sub(rf"\b{re.escape(alias)}\b", real, t, flags=re.I)
        return t
    except Exception:
        return text

def extract_skills(resume_text: str) -> List[str]:
    from .skills_catalog import CORE_SKILLS
    txt = _apply_aliases(_normalize_lower(resume_text))
    found = set()
    if _NLP is not None and _PHRASE_MATCHER is not None:
        doc = _NLP(txt)
        matches = _PHRASE_MATCHER(doc)
        for _, start, end in matches:
            span = doc[start:end].text.lower()
            if span in CORE_SKILLS:
                found.add(span)
    for skill in CORE_SKILLS:
        if re.search(rf"\b{re.escape(skill)}\b", txt, flags=re.I):
            found.add(skill)
    return sorted(found)

def parse_resume_structured(resume_text: str) -> Dict[str, Any]:
    txt_raw = _normalize(resume_text)
    txt = _apply_aliases(txt_raw)
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    email = None
    m = EMAIL_RE.search(txt)
    if m:
        email = m.group(0)
    phones = []
    for match in phonenumbers.PhoneNumberMatcher(txt, "IN"):
        try:
            phones.append(phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.INTERNATIONAL))
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
    edu_lines = [l for l in lines if re.search(r"\b(b\.?tech|btech|be|b\.e\.|bsc|b\.sc|bca|mca|mtech|m\.?tech|mba|bba|phd|diploma|intermediate|12th|10th)\b", l, re.I)]
    skills = extract_skills(txt)
    return {"name": name, "email": email, "phones": phones, "skills": skills, "education_snippets": edu_lines[:5]}
