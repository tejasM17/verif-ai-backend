from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class VerificationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class AgentType(str, Enum):
    RESUME = "resume"
    CERTIFICATE = "certificate"
    GITHUB = "github"


class ResearchLog(BaseModel):
    agent: str
    action: str
    message: str
    details: Optional[str] = None
    timestamp: Optional[datetime] = None


class EvidenceItem(BaseModel):
    agent: str
    category: str
    description: str
    source: Optional[str] = None
    relevance: Optional[str] = None


class AgentResult(BaseModel):
    score: float = 0.0
    confidence: float = 0.0
    summary: str = ""
    red_flags: list[str] = Field(default_factory=list)
    details: dict = Field(default_factory=dict)


class GraphState(BaseModel):
    application_id: str = ""
    student_id: str = ""
    firebase_uid: str = ""
    company_id: str = ""
    resume_text: Optional[str] = None
    certificate_text: Optional[str] = None
    github_raw_data: Optional[dict] = None
    resume_result: Optional[AgentResult] = None
    certificate_result: Optional[AgentResult] = None
    github_result: Optional[AgentResult] = None
    overall_result: Optional[dict] = None
    research_logs: list[ResearchLog] = Field(default_factory=list)
    evidence_items: list[EvidenceItem] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    status: VerificationStatus = VerificationStatus.PENDING


class VerificationResult(BaseModel):
    id: str = ""
    application_id: str = ""
    student_id: str = ""
    firebase_uid: str = ""
    company_id: str = ""
    version: int = 1
    status: VerificationStatus = VerificationStatus.PENDING
    overall_score: Optional[float] = None
    resume_score: Optional[float] = None
    certificate_score: Optional[float] = None
    github_score: Optional[float] = None
    confidence: Optional[float] = None
    verdict: Optional[str] = None
    summary: Optional[str] = None
    research_logs: list[dict] = Field(default_factory=list)
    evidence_items: list[dict] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    resume_details: Optional[dict] = None
    certificate_details: Optional[dict] = None
    github_details: Optional[dict] = None
    error_details: Optional[dict] = None
    timestamps: Optional[dict] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
