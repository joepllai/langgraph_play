from pydantic import BaseModel
from langchain.agents import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from app.agent.prompts.agent_prompts.fhir_agent import FHIR_AGENT_PROMPTS
from app.agent.llm_models import gemini_2_5
from app.utils.apiHelper import ApiHelper

memory = MemorySaver()


class FHIRResponse(BaseModel):
    original_query: str
    response: str
    status: str
    error: str = None

@tool
async def calling_fhir(params: dict) -> dict:
    """
    Build and send an HTTP GET request to the FHIR API using the provided parameters.

    This function constructs the request path using the given resource type and optional
    resource ID, then sends the request. Query parameters are passed along if provided.

    Args:
        params (dict): A dictionary containing FHIR query parameters
            - resource_type (str): The FHIR resource type
                (e.g., 'Patient', 'Observation')
            - resource_id (str, optional): The specific resource ID
            - query_params (dict, optional): Additional query parameters

    Returns:
        dict: A dictionary containing the status and data of the response
            - status: "success" or "error"
            - data (str or None): The raw response body as text if successful.
            - error: Error message if the request failed
    """
    print("Calling FHIR API with params:", params)

    # Build the resource path
    resource_path = params.get("resource_type", "")
    if resource_id := params.get("resource_id"):
        resource_path = f"{resource_path}/{resource_id}"

    # Construct the full URL
    url = f"CP_V3/{resource_path}"

    # Add query parameters if they exist
    query_params = params.get("query_params", {})
    response_text = await ApiHelper().getFHIR(url=url, params=query_params)
    if response_text is None:
        return {
            "status": "error",
            "data": None,
            "error": "Failed to fetch data from FHIR API",
        }

    return {"status": "success", "data": response_text, "error": None}


fhir_agent = create_react_agent(
    name="fhir_agent",
    model=gemini_2_5,
    tools=[calling_fhir],
    response_format=FHIRResponse,
    prompt=FHIR_AGENT_PROMPTS,
    checkpointer=memory,
)
