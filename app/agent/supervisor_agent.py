from langgraph_supervisor import create_supervisor
from app.agent.llm_models import gemini_2_5
from app.agent.fhir_agent import fhir_agent
from app.agent.rag_agent import rag_agent


tool_map = {
    "rag-agent": rag_agent,
    "fhir-agent": fhir_agent,
}

supervisor = create_supervisor(llm=gemini_2_5, agents=tool_map)
