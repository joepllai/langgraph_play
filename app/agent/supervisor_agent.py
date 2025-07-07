from typing import Optional, List
from langgraph_supervisor import create_supervisor
from pydantic import BaseModel
from app.agent.llm_models import gemini_2_5, azure_foundry_gpt_4o
from app.agent.fhir_agent import fhir_agent
from app.agent.rag_agent import rag_agent
from app.agent.web_search_agent import web_search_agent
from app.agent.prompts.agent_prompts.supervisor_agent import SUPERVISOR_AGENT_PROMPT


class SupervisorResponse(BaseModel):
    """Flexible response model for the supervisor agent."""
    answer: str  # The main answer or pass-through from sub-agent
    source_url: str  # The FHIR API endpoints used by the fhir-agent related to this question
    clarification: Optional[str] = None  # If clarification is needed
    context: Optional[List[str]] = None  # Any supporting context or details
    agent: Optional[str] = None  # (Optional) Which sub-agent produced the answer


supervisor_graph = create_supervisor(
    model=azure_foundry_gpt_4o,
    agents=[fhir_agent, rag_agent, web_search_agent],
    prompt=SUPERVISOR_AGENT_PROMPT,
    response_format=SupervisorResponse,
)
supervisor_agent = supervisor_graph.compile()
