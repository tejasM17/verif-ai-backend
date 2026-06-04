from pydantic import BaseModel
from typing import List, Optional

class AnalysisStartRequest(BaseModel):
    student_uid: str
    resume_document_id: str
    cert_doc_ids: List[str]
    github_url: Optional[str] = None

class AnalysisStartResponse(BaseModel):
    job_id: str
    websocket_url: str
