import json
import logging
from typing import Optional

from app.config.settings import settings

logger = logging.getLogger("verifai")

try:
    import google.generativeai as genai

    genai.configure(api_key=settings.GEMINI_API_KEY)
    GEMINI_AVAILABLE = bool(settings.GEMINI_API_KEY)
except Exception:
    GEMINI_AVAILABLE = False
    logger.warning("Gemini SDK not available or no API key. Using mock mode.")


class GeminiService:

    def __init__(self):
        self.model_name = settings.GEMINI_MODEL
        self.available = GEMINI_AVAILABLE

    async def analyze(self, prompt: str, system_instruction: Optional[str] = None) -> dict:
        if not self.available:
            return self._mock_analysis(prompt)

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    top_p=0.95,
                    max_output_tokens=8192,
                ),
            )
            response = await model.generate_content_async(prompt)

            text = response.text.strip()
            text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return json.loads(text)

        except Exception as e:
            logger.error("Gemini analysis failed: %s", e)
            raise RuntimeError(f"Gemini analysis failed: {e}")

    def _mock_analysis(self, prompt: str) -> dict:
        logger.info("Using mock Gemini analysis")
        if "resume" in prompt.lower():
            return {
                "score": 0.78,
                "confidence": 0.72,
                "summary": "Resume appears well-structured with relevant skills. Some sections may benefit from more detail.",
                "red_flags": ["Employment gap not explained", "Limited quantifiable achievements"],
                "details": {"structure_score": 0.85, "relevance_score": 0.80, "ai_generation_score": 0.15},
            }
        elif "certificate" in prompt.lower():
            return {
                "score": 0.85,
                "confidence": 0.80,
                "summary": "Certificate appears authentic with proper issuer details and formatting.",
                "red_flags": [],
                "details": {"formatting_score": 0.90, "issuer_consistency": 0.85, "ai_generation_score": 0.10},
            }
        elif "github" in prompt.lower() or "git" in prompt.lower():
            return {
                "score": 0.82,
                "confidence": 0.75,
                "summary": "GitHub project shows consistent activity with well-structured code and good documentation.",
                "red_flags": ["Large single commits detected", "Some dependencies are outdated"],
                "details": {"repo_structure": 0.80, "commit_activity": 0.75, "code_quality": 0.85, "skill_alignment": 0.80},
            }
        else:
            return {
                "score": 0.80,
                "confidence": 0.75,
                "summary": "Analysis completed successfully.",
                "red_flags": [],
                "details": {},
            }

    def get_resume_prompt(self, resume_text: str, student_skills: str) -> str:
        return f"""Analyze this resume for AI-driven verification.

Resume text:
{resume_text[:15000]}

Student claimed skills: {student_skills}

Analyze:
1. Score the resume structure and completeness (0-1)
2. Detect if content appears AI-generated (0-1 scale, higher = more likely AI)
3. Compare claims against typical resume evidence patterns
4. Identify red flags (gaps, inconsistencies, suspicious patterns)
5. Rate confidence in the analysis

Return JSON only: {{"score": float, "confidence": float, "summary": str, "red_flags": [str], "details": {{"structure_score": float, "relevance_score": float, "ai_generation_score": float}}}}

IMPORTANT: Do NOT reveal any chain-of-thought or private reasoning. Return only the analysis JSON. No hidden reasoning."""

    def get_certificate_prompt(self, certificate_text: str) -> str:
        return f"""Analyze this certificate for AI-driven verification.

Certificate text:
{certificate_text[:10000]}

Analyze:
1. Score certificate authenticity signals (0-1)
2. Detect suspicious formatting or AI-like generation patterns
3. Check issuer details and consistency
4. Identify red flags
5. Rate confidence

Return JSON only: {{"score": float, "confidence": float, "summary": str, "red_flags": [str], "details": {{"formatting_score": float, "issuer_consistency": float, "ai_generation_score": float}}}}

IMPORTANT: Do NOT reveal any chain-of-thought or private reasoning. Return only the analysis JSON."""

    def get_github_prompt(self, repo_data: dict, student_skills: str) -> str:
        return f"""Analyze this GitHub project for AI-driven verification.

Repository data:
{json.dumps(repo_data, indent=2, default=str)[:15000]}

Student claimed skills: {student_skills}

Analyze:
1. Score repository structure and completeness (0-1)
2. Evaluate commit activity and contribution patterns
3. Assess code quality signals
4. Check consistency with claimed skills
5. Detect AI-like generated code patterns
6. Identify red flags

Return JSON only: {{"score": float, "confidence": float, "summary": str, "red_flags": [str], "details": {{"repo_structure": float, "commit_activity": float, "code_quality": float, "skill_alignment": float}}}}

IMPORTANT: Do NOT reveal any chain-of-thought or private reasoning. Return only the analysis JSON."""

    def get_aggregation_prompt(self, resume: dict, certificate: dict, github: dict) -> str:
        resume_score = resume.get("score", 0) if resume else 0
        cert_score = certificate.get("score", 0) if certificate else 0
        gh_score = github.get("score", 0) if github else 0
        resume_conf = resume.get("confidence", 0) if resume else 0
        cert_conf = certificate.get("confidence", 0) if certificate else 0
        gh_conf = github.get("confidence", 0) if github else 0

        resume_flags = resume.get("red_flags", []) if resume else []
        cert_flags = certificate.get("red_flags", []) if certificate else []
        gh_flags = github.get("red_flags", []) if github else []

        return f"""Aggregate these verification agent results into a final verdict:

Resume Agent:
- Score: {resume_score}
- Confidence: {resume_conf}
- Red flags: {resume_flags}

Certificate Agent:
- Score: {cert_score}
- Confidence: {cert_conf}
- Red flags: {cert_flags}

GitHub Agent:
- Score: {gh_score}
- Confidence: {gh_conf}
- Red flags: {gh_flags}

Calculate:
1. overall_score: weighted average (weight resume=0.35, certificate=0.30, github=0.35)
2. confidence: weighted average of individual confidences
3. verdict: "VERIFIED" if overall_score >= 0.7 and limited red flags, "NEEDS_REVIEW" if >= 0.5, "UNVERIFIED" if < 0.5
4. summary: concise 2-3 sentence explanation for the recruiter

Return JSON only: {{"overall_score": float, "confidence": float, "verdict": str, "summary": str}}

IMPORTANT: Do NOT reveal any chain-of-thought or private reasoning. Return only the aggregation JSON."""
