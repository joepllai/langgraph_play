from pydantic import BaseModel
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from app.agent.prompts.agent_prompts.web_search_agent import WEB_SEARCH_AGENT_PROMPTS
from app.agent.llm_models import gemini_2_5
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper


@tool
def web_search(search_term: str, domain="https://twcore.mohw.gov.tw/") -> str:
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
    search = DuckDuckGoSearchAPIWrapper(max_results=3)

    return search.invoke(f"{search_term} site:{domain}")


class WebSearchResponse(BaseModel):
    """Response model for the web search agent."""

    response: str
    source: str = None


web_search_agent = create_react_agent(
    name="web_search_agent",
    model=gemini_2_5,
    tools=[web_search],
    response_format=WebSearchResponse,
    prompt=WEB_SEARCH_AGENT_PROMPTS,
)
