import httpx
from langchain.tools import tool
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

@tool
async def web_search_tool(query: str) -> str:
    """
    Search the web for information using Brave Search API.
    Useful for verifying company details, skill requirements, or general facts.
    Returns the top 3 results' snippets.
    """
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": settings.BRAVE_API_KEY
            }
            params = {
                "q": query,
                "count": 3
            }
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers=headers,
                params=params,
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            
            results = data.get("web", {}).get("results", [])
            if not results:
                return "No search results found."
            
            formatted_results = []
            for r in results:
                title = r.get("title", "No Title")
                url = r.get("url", "No URL")
                snippet = r.get("description", "No snippet available.")
                formatted_results.append(f"Title: {title}\nURL: {url}\nSnippet: {snippet}")
            
            return "\n\n".join(formatted_results)
    except Exception as e:
        logger.error(f"Web search error: {str(e)}")
        return f"Error during web search: {str(e)}"
