import logging
from app.services.graph.state import VerificationState

logger = logging.getLogger(__name__)

async def supervisor_node(state: VerificationState) -> dict:
    """
    Supervisor node that validates input and prepares the state.
    In this architecture, it acts as a gateway before parallel execution.
    """
    student_uid = state.get("student_uid")
    if not student_uid:
        logger.error("Supervisor: student_uid missing")
        return {"error": "student_uid is required"}
    
    logger.info(f"Supervisor: Starting verification for student {student_uid}")
    return {}
