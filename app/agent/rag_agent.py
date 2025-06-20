from pydantic import BaseModel
from langgraph.prebuilt import create_react_agent
from langchain.tools.retriever import create_retriever_tool
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from app.agent.rag_utils.retriver import fhir_api_docs_retriever
from app.agent.prompts.agent_prompts.rag_agent import RAG_AGENT_PROMPTS
from app.agent.llm_models import gemini_2_5, asus_aoc_gpt

memory = MemorySaver()

fhir_api_docs_retriever_tool = create_retriever_tool(
    retriever=fhir_api_docs_retriever,
    name="fhir_api_docs_retriever_tool",
    description="Retrieves FHIR API documentation based on the query.",
)


@tool
def off_topic():
    """This tool is used to indicate that the query is off-topic and not related to FHIR API documentation."""
    return "This query is off-topic and does not relate to FHIR API documentation."


class RAGResponse(BaseModel):
    """Response model for the RAG agent."""

    response: str
    source: str = None


rag_agent = create_react_agent(
    name="rag_agent",
    model=asus_aoc_gpt,
    tools=[fhir_api_docs_retriever_tool, off_topic],
    response_format=RAGResponse,
    prompt=RAG_AGENT_PROMPTS,
    checkpointer=memory,
)
