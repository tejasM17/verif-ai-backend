import logging
from typing import Optional

from app.verification.models import AgentResult, ResearchLog, EvidenceItem
from app.verification.gemini_service import GeminiService

logger = logging.getLogger("verifai")


class CertificateVerificationAgent:

    def __init__(self):
        self.gemini = GeminiService()

    async def analyze(
        self,
        certificate_text: Optional[str],
    ) -> tuple[AgentResult, list[ResearchLog], list[EvidenceItem]]:
        logs: list[ResearchLog] = []
        evidence: list[EvidenceItem] = []

        if not certificate_text or not certificate_text.strip():
            logs.append(ResearchLog(
                agent="certificate",
                action="skip",
                message="No certificate text available for analysis",
            ))
            return AgentResult(score=0.0, confidence=0.0, summary="No certificate provided", red_flags=["Missing certificate"]), logs, evidence

        logs.append(ResearchLog(
            agent="certificate",
            action="extract",
            message=f"Certificate text extracted ({len(certificate_text)} chars)",
        ))

        try:
            prompt = self.gemini.get_certificate_prompt(certificate_text)
            result = await self.gemini.analyze(prompt)

            agent_result = AgentResult(
                score=min(max(float(result.get("score", 0)), 0), 1),
                confidence=min(max(float(result.get("confidence", 0)), 0), 1),
                summary=result.get("summary", ""),
                red_flags=result.get("red_flags", []),
                details=result.get("details", {}),
            )

            logs.append(ResearchLog(
                agent="certificate",
                action="analyze",
                message=f"Certificate score: {agent_result.score:.2f}, confidence: {agent_result.confidence:.2f}",
                details=f"Red flags: {len(agent_result.red_flags)} found",
            ))

            evidence.append(EvidenceItem(
                agent="certificate",
                category="formatting",
                description=f"Formatting score: {result.get('details', {}).get('formatting_score', 'N/A')}",
                relevance="Indicates certificate presentation quality",
            ))

            if result.get("details", {}).get("ai_generation_score", 0) > 0.5:
                evidence.append(EvidenceItem(
                    agent="certificate",
                    category="ai_generation",
                    description=f"AI generation likelihood: {result['details']['ai_generation_score']:.2f}",
                    relevance="Certificate content may be AI-generated",
                ))

            return agent_result, logs, evidence

        except Exception as e:
            logger.error("Certificate verification failed: %s", e)
            logs.append(ResearchLog(
                agent="certificate",
                action="error",
                message=f"Certificate analysis failed: {str(e)}",
            ))
            return AgentResult(
                score=0.0, confidence=0.0,
                summary="Certificate analysis encountered an error",
                red_flags=["Analysis error"],
            ), logs, evidence
