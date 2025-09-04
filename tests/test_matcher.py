from app.services.matcher import match_jobs

def test_matcher_basic():
    results = match_jobs(["python","flask"])
    assert any(r["title"].lower().startswith("software engineer") for r in results)
