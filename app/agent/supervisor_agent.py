from langgraph_supervisor import create_supervisor
from app.agent.llm_models import gemini_2_5
from app.agent.fhir_agent import fhir_agent


supervisor_graph = create_supervisor(
    model=gemini_2_5,
    agents=[fhir_agent],
    prompt="you are a helpful assistant that can answer questions about FHIR APIs. If you don't know the answer, you can ask the FHIR agent for help.",
)
supervisor_agent = supervisor_graph.compile()
