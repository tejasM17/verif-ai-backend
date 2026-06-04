import logging
from datetime import datetime
from typing import List, Dict, Any
from app.services.graph.state import VerificationState, ResearchStep, AgentFlag

logger = logging.getLogger(__name__)

async def cross_reference_node(state: VerificationState) -> dict:
    """
    Pure logic node that compares results from all three agents.
    """
    resume_result = state.get("resume_result") or {}
    github_result = state.get("github_result") or {}
    cert_result = state.get("cert_result") or {}
    
    findings = []
    cross_ref_steps = []
    new_flags = []

    # 1. Resume Skills vs GitHub Languages
    skills_claimed = [s.lower() for s in resume_result.get("skills_claimed", [])]
    languages_used = [l.lower() for l in github_result.get("languages_used", [])]
    
    if skills_claimed and languages_used:
        # Check if major tech skills are missing from GitHub
        common_tech = {"python", "javascript", "typescript", "java", "cpp", "go", "rust", "php", "ruby"}
        claimed_tech = [s for s in skills_claimed if s in common_tech]
        mismatch = [t for t in claimed_tech if t not in languages_used]
        
        if mismatch:
            flag = AgentFlag(
                type="SKILL_GITHUB_MISMATCH",
                detail=f"Resume claims expertise in {mismatch}, but no matching code found on GitHub.",
                severity="high"
            )
            new_flags.append(flag.model_dump())
            findings.append(flag.detail)
        
        cross_ref_steps.append({
            "step": len(cross_ref_steps) + 1,
            "agent": "cross_reference",
            "thought": "Checking if claimed skills match GitHub activity.",
            "action": "set_comparison",
            "query": f"claimed: {claimed_tech}, github: {languages_used}",
            "finding": f"Mismatched tech: {mismatch}" if mismatch else "Skills match GitHub profile.",
            "timestamp": datetime.utcnow().isoformat(),
            "duration_ms": 0,
            "impact": "HIGH" if mismatch else "NEUTRAL",
            "sources": []
        })

    # 2. Timeline Check: GitHub earliest commit vs Resume start dates
    earliest_commits = github_result.get("earliest_commit_by_language", {})
    resume_starts = resume_result.get("experience_start_dates", {})
    
    timeline_violations = []
    for lang, commit_date_str in earliest_commits.items():
        lang_lower = lang.lower()
        for company, start_date_str in resume_starts.items():
            try:
                # Basic ISO comparison YYYY-MM-DD
                if commit_date_str > start_date_str:
                    # If they claim they used Python at Company X starting 2020, 
                    # but GitHub says they first touched Python in 2022.
                    timeline_violations.append(f"{lang} ({commit_date_str}) started AFTER {company} ({start_date_str})")
            except:
                continue
                
    if timeline_violations:
        flag = AgentFlag(
            type="TIMELINE_ANOMALY",
            detail=f"GitHub activity starts after professional claims: {timeline_violations[0]}",
            severity="high"
        )
        new_flags.append(flag.model_dump())
        findings.append(flag.detail)
        
    cross_ref_steps.append({
        "step": len(cross_ref_steps) + 1,
        "agent": "cross_reference",
        "thought": "Verifying if GitHub history supports professional timeline.",
        "action": "timeline_analysis",
        "query": "earliest_commit vs job_start",
        "finding": f"Violations: {timeline_violations}" if timeline_violations else "Timeline is consistent.",
        "timestamp": datetime.utcnow().isoformat(),
        "duration_ms": 0,
        "impact": "HIGH" if timeline_violations else "NEUTRAL",
        "sources": []
    })

    # 3. Cert Course Names vs GitHub Languages
    course_names = [c.lower() for c in cert_result.get("course_names", [])]
    if course_names and languages_used:
        unverified_courses = []
        for course in course_names:
            # Check if any language used on GitHub appears in the course name
            match = any(lang in course for lang in languages_used)
            if not match:
                unverified_courses.append(course)
        
        if unverified_courses:
            flag = AgentFlag(
                type="CERT_WITHOUT_EVIDENCE",
                detail=f"Completed courses {unverified_courses} but no practical application found on GitHub.",
                severity="medium"
            )
            new_flags.append(flag.model_dump())
            findings.append(flag.detail)

        cross_ref_steps.append({
            "step": len(cross_ref_steps) + 1,
            "agent": "cross_reference",
            "thought": "Checking if certificates have practical proof on GitHub.",
            "action": "evidence_check",
            "query": f"courses: {course_names}, languages: {languages_used}",
            "finding": f"Courses lacking evidence: {unverified_courses}" if unverified_courses else "Certificates supported by GitHub activity.",
            "timestamp": datetime.utcnow().isoformat(),
            "duration_ms": 0,
            "impact": "MEDIUM" if unverified_courses else "NEUTRAL",
            "sources": []
        })

    return {
        "cross_ref_findings": findings,
        "research_logs": cross_ref_steps,
        "flags": new_flags
    }
