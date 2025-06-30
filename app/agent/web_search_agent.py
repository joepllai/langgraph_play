import asyncio
from typing import Optional
from langchain_core.tracers.schemas import TracerSessionV1
from pydantic import BaseModel
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from app.agent.prompts.agent_prompts.web_search_agent import WEB_SEARCH_AGENT_PROMPTS
from app.agent.llm_models import azure_foundry_gpt_4o
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_tavily import TavilySearch

# Top-level instances
duckduckgo_search_tool = DuckDuckGoSearchResults()
tavily_search_tool = TavilySearch(
    max_results=5,
    topic="general",
    # Add other fixed params here if desired
)

@tool
async def duck_duck_go_web_search(search_term: str, domain="https://twcore.mohw.gov.tw/") -> str:
    """
    A web search tool that utilizes the DuckDuckGo search engine to query specific domains.

    This tool is designed to perform targeted searches within the specified domain, allowing users to retrieve
    relevant information efficiently. By default, it searches within the "https://twcore.mohw.gov.tw/" domain,
    but the domain can be customized as needed.

    Args:
        search_term (str): The keyword or phrase to search for.
        domain (str, optional): The domain to restrict the search to. Defaults to "https://twcore.mohw.gov.tw/".

    Returns:
        str: A string containing the search results retrieved from the DuckDuckGo API.
    """
    max_retries = 3
    base_delay = 5.0
    
    for attempt in range(max_retries):
        try:
            result = await duckduckgo_search_tool.ainvoke(f"{search_term} site:{domain}")
            return result
        except Exception as e:
            if "202" in str(e) or "rate limit" in str(e).lower():
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    await asyncio.sleep(delay)
                    continue
                else:
                    return f"Rate limit exceeded after {max_retries} attempts. Please try again later."
            else:
                return f"Search error: {str(e)}"
    
    return "Search failed after multiple attempts."


@tool
async def tavily_web_search(search_term: str, domain: str) -> dict:
    """
    A web search tool that utilizes the Tavily Search API.

    Args:
        search_term (str): The keyword or phrase to search for.
        domain (str): The domain to restrict the search to (e.g., 'wikipedia.org').

    Returns:
        dict: A dictionary containing the search results retrieved from the Tavily API. The structure is as follows:
            {
                "query": str,  # The search query
                "follow_up_questions": Optional[list],
                "answer": Optional[str],
                "images": list,
                "results": list[dict],  # Each dict contains 'title', 'url', 'content', etc.
                ...
            }
        Example:
            {
                "query": "euro 2024 host nation",
                "follow_up_questions": null,
                "answer": null,
                "images": [],
                "results": [
                    {
                        "title": "UEFA Euro 2024 - Wikipedia",
                        "url": "https://en.wikipedia.org/wiki/UEFA_Euro_2024",
                        "content": "Tournament details Host country Germany Dates 14 June – 14 July ...",
                        ...
                    },
                    ...
                ],
                "response_time": 1.67
            }

    Usage:
        Use this tool to perform a web search within certain domain and receive a structured response suitable for direct use by an agent or LLM.
    """
    return await tavily_search_tool.ainvoke(input=search_term, include_domains= domain)

class WebSearchResponse(BaseModel):
    """Response model for the web search agent."""

    response: str
    source: Optional[str] = None


web_search_agent = create_react_agent(
    name="web_search_agent",
    model=azure_foundry_gpt_4o,
    tools=[duck_duck_go_web_search, tavily_web_search],
    prompt=WEB_SEARCH_AGENT_PROMPTS,
    response_format=WebSearchResponse
)
