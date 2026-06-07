import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.verification.models import (
    GraphState, AgentResult, ResearchLog, EvidenceItem,
    VerificationResult, VerificationStatus,
)
from app.verification.agents.resume_agent import ResumeVerificationAgent
from app.verification.agents.certificate_agent import CertificateVerificationAgent
from app.verification.agents.github_agent import GitHubVerificationAgent
from app.verification.gemini_service import GeminiService
from app.verification.repository import VerificationRepository

logger = logging.getLogger("verifai")


class VerificationOrchestrator:

    def __init__(self):
        self.repo = VerificationRepository()

    async def run_verification(self, application_id: str, student_id: str, firebase_uid: str, company_id: str) -> VerificationResult:
        state = GraphState(
            application_id=application_id,
            student_id=student_id,
            firebase_uid=firebase_uid,
            company_id=company_id,
            status=VerificationStatus.IN_PROGRESS,
        )

        result = await self.repo.find_by_application(application_id)
        if result and result.status == VerificationStatus.IN_PROGRESS:
            raise RuntimeError("Verification already in progress for this application")
        if result and result.status == VerificationStatus.COMPLETED:
            result.version += 1
            result.status = VerificationStatus.IN_PROGRESS
            await self.repo.save(result)
        else:
            timestamp = datetime.now(timezone.utc)
            doc_id = str(uuid.uuid4())
            result = VerificationResult(
                id=doc_id,
                application_id=application_id,
                student_id=student_id,
                firebase_uid=firebase_uid,
                company_id=company_id,
                version=1,
                status=VerificationStatus.IN_PROGRESS,
                created_at=timestamp,
                updated_at=timestamp,
            )
            await self.repo.save(result)

        await self._update_progress(application_id, "initialized", "Verification started")

        try:
            student_data = await self._get_student_data(firebase_uid)
            resume_text = await self._extract_file_text(application_id, "resume")
            certificate_text = await self._extract_file_text(application_id, "certificate")
            github_url = student_data.get("github_url") or ""

            app_data = await self.repo.db.collection("applications").document(application_id).get()
            if app_data.exists:
                app_dict = app_data.to_dict()
                github_url = github_url or app_dict.get("github_project_link", "")

            student_skills = student_data.get("skills", "") if student_data else ""

            state.resume_text = resume_text
            state.certificate_text = certificate_text

            await self._update_progress(application_id, "extracting", "Files extracted, starting agent analysis")

            resume_task = self._run_resume_agent(resume_text, student_skills, state)
            cert_task = self._run_certificate_agent(certificate_text, state)
            github_task = self._run_github_agent(github_url, student_skills, state)

            resume_result, cert_result, github_result = await asyncio.gather(
                resume_task, cert_task, github_task, return_exceptions=True,
            )

            if isinstance(resume_result, Exception):
                state.errors.append(f"Resume agent failed: {resume_result}")
                resume_result = AgentResult(score=0.0, confidence=0.0, summary="Failed", red_flags=["Agent error"])
                await self._update_progress(application_id, "error", f"Resume agent error: {resume_result}")
            if isinstance(cert_result, Exception):
                state.errors.append(f"Certificate agent failed: {cert_result}")
                cert_result = AgentResult(score=0.0, confidence=0.0, summary="Failed", red_flags=["Agent error"])
                await self._update_progress(application_id, "error", f"Certificate agent error: {cert_result}")
            if isinstance(github_result, Exception):
                state.errors.append(f"GitHub agent failed: {github_result}")
                github_result = AgentResult(score=0.0, confidence=0.0, summary="Failed", red_flags=["Agent error"])
                await self._update_progress(application_id, "error", f"GitHub agent error: {github_result}")

            state.resume_result = resume_result if not isinstance(resume_result, Exception) else resume_result
            state.certificate_result = cert_result if not isinstance(cert_result, Exception) else cert_result
            state.github_result = github_result if not isinstance(github_result, Exception) else github_result

            await self._update_progress(application_id, "aggregating", "Aggregating results from all agents")

            aggregate_result = await self._aggregate_results(state)

            state.overall_result = aggregate_result

            num_errors = len(state.errors)
            if num_errors > 0:
                state.status = VerificationStatus.PARTIAL
            else:
                state.status = VerificationStatus.COMPLETED

            timestamp = datetime.now(timezone.utc)
            timestamps = {
                "started": result.created_at.isoformat() if result.created_at else "",
                "resume_completed": timestamp.isoformat(),
                "certificate_completed": timestamp.isoformat(),
                "github_completed": timestamp.isoformat(),
                "aggregation_completed": timestamp.isoformat(),
                "completed": timestamp.isoformat(),
            }

            source_urls = []
            for e in state.evidence_items:
                if e.source and e.source not in source_urls:
                    source_urls.append(e.source)

            verification_result = VerificationResult(
                id=result.id,
                application_id=application_id,
                student_id=student_id,
                firebase_uid=firebase_uid,
                company_id=company_id,
                version=result.version,
                status=state.status,
                overall_score=aggregate_result.get("overall_score"),
                resume_score=state.resume_result.score if state.resume_result else None,
                certificate_score=state.certificate_result.score if state.certificate_result else None,
                github_score=state.github_result.score if state.github_result else None,
                confidence=aggregate_result.get("confidence"),
                verdict=aggregate_result.get("verdict"),
                summary=aggregate_result.get("summary"),
                research_logs=[log.model_dump(mode="json") for log in state.research_logs],
                evidence_items=[e.model_dump(mode="json") for e in state.evidence_items],
                source_urls=source_urls,
                resume_details=state.resume_result.details if state.resume_result else None,
                certificate_details=state.certificate_result.details if state.certificate_result else None,
                github_details=state.github_result.details if state.github_result else None,
                error_details={"errors": state.errors} if state.errors else None,
                timestamps=timestamps,
                is_active=True,
                created_at=result.created_at,
                updated_at=timestamp,
            )

            await self.repo.save(verification_result)
            await self._update_progress(application_id, "completed", "Verification completed")

            return verification_result

        except Exception as e:
            logger.error("Verification orchestration failed: %s", e, exc_info=True)
            timestamp = datetime.now(timezone.utc)

            verification_result = VerificationResult(
                id=result.id,
                application_id=application_id,
                student_id=student_id,
                firebase_uid=firebase_uid,
                company_id=company_id,
                version=result.version,
                status=VerificationStatus.FAILED,
                error_details={"errors": [str(e)]},
                timestamps={"failed": timestamp.isoformat()},
                created_at=result.created_at,
                updated_at=timestamp,
            )
            await self.repo.save(verification_result)
            await self._update_progress(application_id, "failed", f"Verification failed: {str(e)}")
            return verification_result

    async def _run_resume_agent(self, resume_text: Optional[str], student_skills: str, state: GraphState) -> AgentResult:
        agent = ResumeVerificationAgent()
        result, logs, evidence = await agent.analyze(resume_text, student_skills)
        state.research_logs.extend(logs)
        state.evidence_items.extend(evidence)
        return result

    async def _run_certificate_agent(self, certificate_text: Optional[str], state: GraphState) -> AgentResult:
        agent = CertificateVerificationAgent()
        result, logs, evidence = await agent.analyze(certificate_text)
        state.research_logs.extend(logs)
        state.evidence_items.extend(evidence)
        return result

    async def _run_github_agent(self, github_url: str, student_skills: str, state: GraphState) -> AgentResult:
        agent = GitHubVerificationAgent()
        try:
            result, logs, evidence = await agent.analyze(github_url, student_skills)
            state.research_logs.extend(logs)
            state.evidence_items.extend(evidence)
            return result
        finally:
            await agent.close()

    async def _aggregate_results(self, state: GraphState) -> dict:
        resume = state.resume_result
        certificate = state.certificate_result
        github = state.github_result

        if not resume and not certificate and not github:
            return {
                "overall_score": 0.0,
                "confidence": 0.0,
                "verdict": "UNVERIFIED",
                "summary": "No agent results available",
            }

        resume_score = resume.score if resume else 0
        cert_score = certificate.score if certificate else 0
        gh_score = github.score if github else 0
        resume_conf = resume.confidence if resume else 0
        cert_conf = certificate.confidence if certificate else 0
        gh_conf = github.confidence if github else 0

        try:
            gemini = GeminiService()
            prompt = gemini.get_aggregation_prompt(
                {"score": resume_score, "confidence": resume_conf, "red_flags": resume.red_flags if resume else []},
                {"score": cert_score, "confidence": cert_conf, "red_flags": certificate.red_flags if certificate else []},
                {"score": gh_score, "confidence": gh_conf, "red_flags": github.red_flags if github else []},
            )
            result = await gemini.analyze(prompt)
            return result
        except Exception as e:
            logger.warning("Gemini aggregation failed, using fallback: %s", e)

        has_resume = resume_text_available(state.resume_text)
        has_cert = cert_text_available(state.certificate_text)
        num_agents = sum([1 for x in [has_resume, has_cert, True] if x])

        if num_agents == 0:
            return {
                "overall_score": 0.0,
                "confidence": 0.0,
                "verdict": "UNVERIFIED",
                "summary": "No data available for verification",
            }

        weights = {"resume": 0.35, "certificate": 0.30, "github": 0.35}
        if not has_resume:
            weights = {"resume": 0, "certificate": 0.45, "github": 0.55}
        if not has_cert:
            weights = {"resume": 0.50, "certificate": 0, "github": 0.50}

        total_weight = sum(weights.values())
        if total_weight > 0:
            overall_score = (
                resume_score * weights["resume"]
                + cert_score * weights["certificate"]
                + gh_score * weights["github"]
            ) / total_weight
            confidence = (
                resume_conf * weights["resume"]
                + cert_conf * weights["certificate"]
                + gh_conf * weights["github"]
            ) / total_weight
        else:
            overall_score = 0
            confidence = 0

        all_flags = []
        if resume and resume.red_flags:
            all_flags.extend(resume.red_flags)
        if certificate and certificate.red_flags:
            all_flags.extend(certificate.red_flags)
        if github and github.red_flags:
            all_flags.extend(github.red_flags)

        if overall_score >= 0.7 and len(all_flags) <= 2:
            verdict = "VERIFIED"
        elif overall_score >= 0.5:
            verdict = "NEEDS_REVIEW"
        else:
            verdict = "UNVERIFIED"

        return {
            "overall_score": round(overall_score, 2),
            "confidence": round(confidence, 2),
            "verdict": verdict,
            "summary": f"Verification {verdict.lower()}. Overall score: {overall_score:.2f} with {confidence:.2f} confidence. {len(all_flags)} red flag(s) identified.",
        }

    async def _extract_file_text(self, application_id: str, file_type: str) -> Optional[str]:
        try:
            from app.repositories.file_repository import FileRepository
            file_repo = FileRepository()
            doc = await file_repo.find_by_application_and_type(application_id, file_type)
            if not doc or "file_data" not in doc:
                return None

            file_data = doc["file_data"]
            if isinstance(file_data, bytes):
                try:
                    import PyPDF2
                    import io
                    pdf_file = io.BytesIO(file_data)
                    reader = PyPDF2.PdfReader(pdf_file)
                    text = "\n".join(page.extract_text() or "" for page in reader.pages)
                    if text.strip():
                        return text
                except Exception:
                    pass

                try:
                    text = file_data.decode("utf-8", errors="ignore")
                    if text.strip():
                        return text[:20000]
                except Exception:
                    pass

            return f"[{file_type.upper()} FILE - {doc.get('original_filename', 'unknown')} - {doc.get('file_size', 0)} bytes]"

        except Exception as e:
            logger.warning("Failed to extract %s text: %s", file_type, e)
            return None

    async def _get_student_data(self, firebase_uid: str) -> Optional[dict]:
        try:
            from app.repositories.student import StudentRepository
            student_repo = StudentRepository()
            student = await student_repo.get_by_firebase_uid(firebase_uid)
            return student.model_dump() if student else None
        except Exception as e:
            logger.warning("Failed to get student data: %s", e)
            return None

    async def _update_progress(self, application_id: str, stage: str, message: str):
        try:
            collection = self.repo.db.collection("verification_progress")
            await asyncio.to_thread(
                lambda: collection.document(application_id).set({
                    "application_id": application_id,
                    "stage": stage,
                    "message": message,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            )
        except Exception as e:
            logger.warning("Failed to update progress: %s", e)

    async def get_verification(self, application_id: str) -> Optional[VerificationResult]:
        return await self.repo.find_by_application(application_id)

    async def get_verification_history(self, application_id: str) -> list[VerificationResult]:
        return await self.repo.find_all_by_application(application_id)

    async def get_progress(self, application_id: str) -> Optional[dict]:
        try:
            doc = await asyncio.to_thread(
                lambda: self.repo.db.collection("verification_progress").document(application_id).get()
            )
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception:
            return None


def resume_text_available(text: Optional[str]) -> bool:
    return bool(text and text.strip())


def cert_text_available(text: Optional[str]) -> bool:
    return bool(text and text.strip())
