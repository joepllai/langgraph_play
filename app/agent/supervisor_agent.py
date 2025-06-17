from langgraph_supervisor import create_supervisor
from app.agent.llm_models import gemini_2_5
from app.agent.fhir_agent import fhir_agent
from app.agent.rag_agent import rag_agent


supervisor_agent = create_supervisor(llm=gemini_2_5, agents=[fhir_agent, rag_agent])
