from langgraph_supervisor import create_supervisor
from pydantic import BaseModel
from app.agent.llm_models import gemini_2_5
from app.agent.fhir_agent import fhir_agent
from app.agent.rag_agent import rag_agent
from app.agent.prompts.agent_prompts.supervisor_agent import SUPERVISOR_AGENT_PROMPT


class SupervisorResponse(BaseModel):
    """Response model for the supervisor agent."""
    response: str

supervisor_graph = create_supervisor(
    model=gemini_2_5,
    agents=[fhir_agent, rag_agent],
    prompt=SUPERVISOR_AGENT_PROMPT,
    response_format=SupervisorResponse,
)
supervisor_agent = supervisor_graph.compile()
