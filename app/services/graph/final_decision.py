import logging
import uuid
from datetime import datetime
from app.services.graph.state import VerificationState
from app.core.firebase import get_firestore
from app.services.trust_score import calculate_trust_score, get_verdict

logger = logging.getLogger(__name__)

async def final_decision_node(state: VerificationState) -> dict:
    """
    Calculates final trust score and saves to database.
    """
    student_uid = state.get("student_uid")
    resume_result = state.get("resume_result") or {}
    cert_result = state.get("cert_result") or {}
    github_result = state.get("github_result") or {}
    
    r_score = resume_result.get("overall_resume_trust", 50.0)
    c_score = cert_result.get("overall_cert_trust", 50.0)
    g_score = github_result.get("overall_github_trust", 50.0)
    
    trust_score = calculate_trust_score(r_score, c_score, g_score)
    verdict = get_verdict(trust_score)
        
    try:
        db = get_firestore()
        verification_id = str(uuid.uuid4())
        
        verification_data = {
            "student_uid": student_uid,
            "trust_score": trust_score,
            "verdict": verdict,
            "resume_score": r_score,
            "cert_score": c_score,
            "github_score": g_score,
            "flags": state.get("flags", []),
            "cross_ref_findings": state.get("cross_ref_findings", []),
            "created_at": datetime.utcnow()
        }
        
        # Save to /verifications
        await db.collection("verifications").document(verification_id).set(verification_data)
        
        # Update /profiles
        profile_ref = db.collection("profiles").document(student_uid)
        await profile_ref.set({
            "trust_score": trust_score,
            "verdict": verdict,
            "verification_id": verification_id,
            "verified_at": datetime.utcnow()
        }, merge=True)
        
    except Exception as e:
        logger.error(f"Failed to save final decision to Firestore: {str(e)}")

    return {
        "overall_trust_score": trust_score,
        "verdict": verdict
    }
