from github import Github
from langchain.tools import tool
from app.core.config import settings
from datetime import datetime, timezone
import logging
import re
from typing import List

logger = logging.getLogger(__name__)

def _get_github_client():
    return Github(settings.GITHUB_TOKEN)

def _extract_username(github_url: str) -> str:
    # Handles https://github.com/username or github.com/username
    match = re.search(r"github\.com/([^/]+)", github_url)
    if match:
        return match.group(1)
    return github_url.split("/")[-1]

@tool
async def get_github_profile(github_url: str) -> dict:
    """
    Retrieves basic GitHub profile information.
    """
    try:
        g = _get_github_client()
        username = _extract_username(github_url)
        user = g.get_user(username)
        
        account_age = (datetime.now(timezone.utc) - user.created_at.replace(tzinfo=timezone.utc)).days
        
        return {
            "username": user.login,
            "account_age_days": account_age,
            "public_repos": user.public_repos,
            "followers": user.followers,
            "bio": user.bio,
            "blog": user.blog
        }
    except Exception as e:
        logger.error(f"GitHub profile error: {str(e)}")
        return {"error": str(e)}

@tool
async def analyze_github_repos(github_url: str) -> dict:
    """
    Analyzes repository distribution, fork ratio, and languages.
    """
    try:
        g = _get_github_client()
        username = _extract_username(github_url)
        user = g.get_user(username)
        repos = user.get_repos()
        
        total_repos = 0
        forks = 0
        languages = {}
        readme_only_count = 0
        stars = 0
        
        for repo in repos:
            total_repos += 1
            if repo.fork:
                forks += 1
            
            stars += repo.stargazers_count
            
            lang = repo.language
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
            
            # Simple check for "readme-only" - very low size
            if repo.size < 10: # KiloBytes
                readme_only_count += 1
                
        return {
            "total_repos": total_repos,
            "fork_ratio": forks / total_repos if total_repos > 0 else 0,
            "language_distribution": languages,
            "readme_only_count": readme_only_count,
            "avg_stars": stars / total_repos if total_repos > 0 else 0
        }
    except Exception as e:
        logger.error(f"GitHub repo analysis error: {str(e)}")
        return {"error": str(e)}

def compute_burst_score(dates: List[datetime]) -> float:
    """Measures how 'bursty' the commits are. High burstiness = suspicious."""
    if len(dates) < 2:
        return 0.0
    
    # Sort dates
    sorted_dates = sorted(dates)
    intervals = []
    for i in range(1, len(sorted_dates)):
        delta = (sorted_dates[i] - sorted_dates[i-1]).total_seconds()
        intervals.append(delta)
    
    import statistics
    mean_interval = statistics.mean(intervals)
    if mean_interval == 0:
        return 1.0 # Everything happened at once
    
    stdev_interval = statistics.stdev(intervals)
    return stdev_interval / mean_interval

def compute_commit_message_quality(messages: List[str]) -> float:
    """Scores commit message descriptiveness."""
    if not messages:
        return 0.0
        
    score = 0
    patterns = {
        r"^(feat|fix|bug|refactor|test|docs|style|chore)": 1.0,
        r"^(update|edit|save|commit|change|added)": 0.2,
        r"^[asdfjkl;]+$": -0.5,
        r"^(\.|\!|\?)$": -1.0
    }
    
    for msg in messages:
        msg_lower = msg.lower()
        matched = False
        for pattern, weight in patterns.items():
            if re.match(pattern, msg_lower):
                score += weight
                matched = True
                break
        if not matched and len(msg) > 10:
            score += 0.5
            
    return max(0.0, min(1.0, score / len(messages)))

@tool
async def analyze_commit_patterns(github_url: str) -> dict:
    """
    Analyzes commit frequency, message quality, and temporal distribution.
    """
    try:
        g = _get_github_client()
        username = _extract_username(github_url)
        user = g.get_user(username)
        
        # Get top 10 repos by star count
        repos = sorted(list(user.get_repos()), key=lambda x: x.stargazers_count, reverse=True)[:10]
        
        all_commit_dates = []
        all_messages = []
        hours = [0] * 24
        earliest_commits = {} # {lang: date}
        
        for repo in repos:
            if repo.fork: continue
            
            try:
                commits = repo.get_commits()
                # Sample last 50 commits per repo
                for commit in commits[:50]:
                    c_date = commit.commit.author.date.replace(tzinfo=timezone.utc)
                    all_commit_dates.append(c_date)
                    all_messages.append(commit.commit.message)
                    hours[c_date.hour] += 1
                    
                    lang = repo.language
                    if lang:
                        if lang not in earliest_commits or c_date < earliest_commits[lang]:
                            earliest_commits[lang] = c_date
            except:
                continue # Skip private or empty repos
                
        return {
            "burst_score": compute_burst_score(all_commit_dates),
            "msg_quality_score": compute_commit_message_quality(all_messages),
            "hour_distribution": hours,
            "earliest_commit_by_language": {k: v.isoformat() for k, v in earliest_commits.items()}
        }
    except Exception as e:
        logger.error(f"GitHub commit analysis error: {str(e)}")
        return {"error": str(e)}
