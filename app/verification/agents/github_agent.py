import json
import logging
import re
from typing import Optional

import httpx

from app.verification.models import AgentResult, ResearchLog, EvidenceItem
from app.verification.gemini_service import GeminiService

logger = logging.getLogger("verifai")

GITHUB_API_BASE = "https://api.github.com"


class GitHubVerificationAgent:

    def __init__(self):
        self.gemini = GeminiService()
        self.http_client = httpx.AsyncClient(timeout=15.0)

    async def fetch_repo_data(self, github_url: str) -> Optional[dict]:
        repo_path = self._parse_github_url(github_url)
        if not repo_path:
            return None

        try:
            repo_resp = await self.http_client.get(f"{GITHUB_API_BASE}/repos/{repo_path}")
            if repo_resp.status_code == 403:
                logger.warning("GitHub API rate limit reached for %s", repo_path)
                return {"error": "GITHUB_API_LIMIT", "repo_path": repo_path}
            if repo_resp.status_code == 404:
                logger.warning("GitHub repo not found: %s", repo_path)
                return {"error": "REPO_NOT_FOUND", "repo_path": repo_path}
            if repo_resp.status_code != 200:
                logger.warning("GitHub API error %d for %s", repo_resp.status_code, repo_path)
                return {"error": f"HTTP_{repo_resp.status_code}", "repo_path": repo_path}

            repo_data = repo_resp.json()

            commits_resp = await self.http_client.get(
                f"{GITHUB_API_BASE}/repos/{repo_path}/commits",
                params={"per_page": 30},
            )
            commits = commits_resp.json() if commits_resp.status_code == 200 else []

            contents_resp = await self.http_client.get(
                f"{GITHUB_API_BASE}/repos/{repo_path}/contents",
            )
            contents = contents_resp.json() if contents_resp.status_code == 200 else []

            languages_resp = await self.http_client.get(
                f"{GITHUB_API_BASE}/repos/{repo_path}/languages",
            )
            languages = languages_resp.json() if languages_resp.status_code == 200 else {}

            readme_resp = await self.http_client.get(
                f"{GITHUB_API_BASE}/repos/{repo_path}/readme",
            )
            readme_data = readme_resp.json() if readme_resp.status_code == 200 else {}

            return {
                "name": repo_data.get("name", ""),
                "description": repo_data.get("description", ""),
                "topics": repo_data.get("topics", []),
                "language": repo_data.get("language", ""),
                "languages": languages,
                "stars": repo_data.get("stargazers_count", 0),
                "forks": repo_data.get("forks_count", 0),
                "open_issues": repo_data.get("open_issues_count", 0),
                "created_at": repo_data.get("created_at", ""),
                "updated_at": repo_data.get("updated_at", ""),
                "pushed_at": repo_data.get("pushed_at", ""),
                "size": repo_data.get("size", 0),
                "has_readme": bool(readme_data.get("content", "")),
                "has_license": bool(repo_data.get("license")),
                "commits_count": len(commits),
                "recent_commits": [
                    {
                        "sha": c["sha"][:8],
                        "message": c["commit"]["message"][:100],
                        "author": c["commit"]["author"]["name"],
                        "date": c["commit"]["author"]["date"],
                    }
                    for c in commits[:10]
                ],
                "top_files": [
                    {"name": f.get("name", ""), "type": f.get("type", "")}
                    for f in (contents[:20] if isinstance(contents, list) else [])
                ],
            }

        except httpx.TimeoutException:
            logger.warning("GitHub API timeout for %s", github_url)
            return {"error": "TIMEOUT", "repo_path": repo_path}
        except Exception as e:
            logger.warning("GitHub fetch failed for %s: %s", github_url, e)
            return {"error": str(e), "repo_path": repo_path}

    def _parse_github_url(self, url: str) -> Optional[str]:
        if not url:
            return None
        patterns = [
            r"github\.com/([^/]+/[^/]+?)(?:/.*)?$",
            r"github\.com/([^/]+/[^/]+?)$",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                path = match.group(1).rstrip("/").rstrip(".git")
                if path.count("/") == 1:
                    return path
        return None

    async def analyze(
        self,
        github_url: str,
        student_skills: str = "",
    ) -> tuple[AgentResult, list[ResearchLog], list[EvidenceItem]]:
        logs: list[ResearchLog] = []
        evidence: list[EvidenceItem] = []

        if not github_url:
            logs.append(ResearchLog(
                agent="github",
                action="skip",
                message="No GitHub URL provided",
            ))
            return AgentResult(score=0.0, confidence=0.0, summary="No GitHub link provided", red_flags=["Missing GitHub link"]), logs, evidence

        repo_path = self._parse_github_url(github_url)
        if not repo_path:
            logs.append(ResearchLog(
                agent="github",
                action="error",
                message=f"Invalid GitHub URL: {github_url}",
            ))
            return AgentResult(
                score=0.0, confidence=0.0,
                summary="Invalid GitHub URL format",
                red_flags=["Invalid GitHub URL"],
            ), logs, evidence

        logs.append(ResearchLog(
            agent="github",
            action="fetch",
            message=f"Fetching GitHub repository: {repo_path}",
        ))

        repo_data = await self.fetch_repo_data(github_url)

        if repo_data is None:
            logs.append(ResearchLog(
                agent="github",
                action="error",
                message="Failed to fetch GitHub repository data",
            ))
            return AgentResult(
                score=0.0, confidence=0.0,
                summary="Could not access GitHub repository",
                red_flags=["Repository access failed"],
            ), logs, evidence

        if "error" in repo_data:
            error = repo_data["error"]
            logs.append(ResearchLog(
                agent="github",
                action="error",
                message=f"GitHub API error: {error}",
            ))
            return AgentResult(
                score=0.0, confidence=0.0,
                summary=f"GitHub repository error: {error}",
                red_flags=[f"GitHub error: {error}"],
            ), logs, evidence

        logs.append(ResearchLog(
            agent="github",
            action="data",
            message=f"Repository found: {repo_data.get('name', '')} ({repo_data.get('language', '')})",
            details=f"Stars: {repo_data.get('stars', 0)}, Commits sampled: {repo_data.get('commits_count', 0)}",
        ))

        try:
            prompt = self.gemini.get_github_prompt(repo_data, student_skills)
            result = await self.gemini.analyze(prompt)

            agent_result = AgentResult(
                score=min(max(float(result.get("score", 0)), 0), 1),
                confidence=min(max(float(result.get("confidence", 0)), 0), 1),
                summary=result.get("summary", ""),
                red_flags=result.get("red_flags", []),
                details=result.get("details", {}),
            )

            logs.append(ResearchLog(
                agent="github",
                action="analyze",
                message=f"GitHub score: {agent_result.score:.2f}, confidence: {agent_result.confidence:.2f}",
                details=f"Red flags: {len(agent_result.red_flags)} found",
            ))

            evidence.append(EvidenceItem(
                agent="github",
                category="repo_structure",
                description=f"Repo structure score: {result.get('details', {}).get('repo_structure', 'N/A')}",
                relevance="Indicates project organization quality",
            ))
            evidence.append(EvidenceItem(
                agent="github",
                category="commit_activity",
                description=f"Commit activity score: {result.get('details', {}).get('commit_activity', 'N/A')}",
                relevance="Shows development consistency",
            ))

            evidence.append(EvidenceItem(
                agent="github",
                category="source_url",
                description=f"Source: {github_url}",
                relevance="Original repository URL",
            ))

            return agent_result, logs, evidence

        except Exception as e:
            logger.error("GitHub analysis failed: %s", e)
            logs.append(ResearchLog(
                agent="github",
                action="error",
                message=f"GitHub analysis failed: {str(e)}",
            ))
            return AgentResult(
                score=0.0, confidence=0.0,
                summary="GitHub analysis encountered an error",
                red_flags=["Analysis error"],
            ), logs, evidence

    async def close(self):
        await self.http_client.aclose()
