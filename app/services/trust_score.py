def calculate_trust_score(resume_score: float, cert_score: float, github_score: float) -> float:
    """
    Standard trust score formula: resume×0.40 + cert×0.35 + github×0.25
    """
    return (resume_score * 0.40) + (cert_score * 0.35) + (github_score * 0.25)

def get_verdict(trust_score: float) -> str:
    """
    Determines verdict based on trust score.
    ≥80→AUTHENTIC, 60-79→FLAGGED, 35-59→SUSPICIOUS, <35→FAKE
    """
    if trust_score >= 80:
        return "AUTHENTIC"
    elif trust_score >= 60:
        return "FLAGGED"
    elif trust_score >= 35:
        return "SUSPICIOUS"
    else:
        return "FAKE"
