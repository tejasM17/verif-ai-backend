import logging
from typing import Optional

from app.verification.models import AgentResult, ResearchLog, EvidenceItem
from app.verification.gemini_service import GeminiService

logger = logging.getLogger("verifai")


class ResumeVerificationAgent:

    def __init__(self):
        self.gemini = GeminiService()

    async def analyze(
        self,
        resume_text: Optional[str],
        student_skills: str = "",
    ) -> tuple[AgentResult, list[ResearchLog], list[EvidenceItem]]:
        logs: list[ResearchLog] = []
        evidence: list[EvidenceItem] = []

        if not resume_text or not resume_text.strip():
            logs.append(ResearchLog(
                agent="resume",
                action="skip",
                message="No resume text available for analysis",
            ))
            return AgentResult(score=0.0, confidence=0.0, summary="No resume provided", red_flags=["Missing resume"]), logs, evidence

        logs.append(ResearchLog(
            agent="resume",
            action="extract",
            message=f"Resume text extracted ({len(resume_text)} chars)",
        ))

        try:
            prompt = self.gemini.get_resume_prompt(resume_text, student_skills)
            result = await self.gemini.analyze(prompt)

            agent_result = AgentResult(
                score=min(max(float(result.get("score", 0)), 0), 1),
                confidence=min(max(float(result.get("confidence", 0)), 0), 1),
                summary=result.get("summary", ""),
                red_flags=result.get("red_flags", []),
                details=result.get("details", {}),
            )

            logs.append(ResearchLog(
                agent="resume",
                action="analyze",
                message=f"Resume score: {agent_result.score:.2f}, confidence: {agent_result.confidence:.2f}",
                details=f"Red flags: {len(agent_result.red_flags)} found",
            ))

            evidence.append(EvidenceItem(
                agent="resume",
                category="structure",
                description=f"Resume structure score: {result.get('details', {}).get('structure_score', 'N/A')}",
                relevance="Indicates resume quality and completeness",
            ))

            if result.get("details", {}).get("ai_generation_score", 0) > 0.5:
                evidence.append(EvidenceItem(
                    agent="resume",
                    category="ai_generation",
                    description=f"AI generation likelihood: {result['details']['ai_generation_score']:.2f}",
                    relevance="Content may be AI-generated",
                ))

            return agent_result, logs, evidence

        except Exception as e:
            logger.error("Resume verification failed: %s", e)
            logs.append(ResearchLog(
                agent="resume",
                action="error",
                message=f"Resume analysis failed: {str(e)}",
            ))
            return AgentResult(
                score=0.0, confidence=0.0,
                summary="Resume analysis encountered an error",
                red_flags=["Analysis error"],
            ), logs, evidence
