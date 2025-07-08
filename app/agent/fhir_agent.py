from pydantic import BaseModel
from langchain.agents import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from typing import Optional, Dict, Any
from urllib.parse import urlencode
import re

from app.agent.prompts.agent_prompts.fhir_agent import (
    FHIR_AGENT_PROMPTS,
    FHIR_AGENT_PROMPT_TEMPLATE,
)
from app.agent.llm_models import gemini_2_5, azure_foundry_gpt_4o
from app.utils.apiHelper import ApiHelper

memory = MemorySaver()


class FHIRResponse(BaseModel):
    data: str
    status: str
    source_url: str  # The actual FHIR endpoint used
    error: str = ""


class FHIRQueryInput(BaseModel):
    resource_type: str
    resource_id: Optional[str] = None
    query_params: Optional[Dict[str, Any]] = None


@tool
async def calling_fhir(params: FHIRQueryInput) -> dict:
    """
    Build and send an HTTP GET request to the FHIR API using the provided parameters.

    Args:
        params (FHIRQueryInput): An object containing FHIR query parameters:
            - resource_type (str): The FHIR resource type (e.g., 'Patient', 'Observation')
            - resource_id (str, optional): The specific resource ID
            - query_params (dict, optional): Additional query parameters for the FHIR API

    Example:
        FHIRQueryInput(
            resource_type="Observation",
            resource_id=None,
            query_params={"code": "12345-6", "date": "ge2024-01-01"}
        )

    Returns:
        dict: A dictionary containing the status and data of the response
            - status: "success" or "error"
            - data (str or None): The raw response body as text if successful.
            - error: Error message if the request failed
    """
    print("Calling FHIR API with params:", params)

    # Build the resource path
    resource_path = params.resource_type
    if resource_id := params.resource_id:
        resource_path = f"{resource_path}/{resource_id}"

    # Add query parameters if they exist
    query_params = params.query_params or {}

    endpoint = resource_path
    if query_params:
        from urllib.parse import urlencode

        endpoint += "?" + urlencode(query_params)

    response_text = await ApiHelper().getFHIR(url=resource_path, params=query_params)
    if response_text is None:
        return {
            "status": "error",
            "data": None,
            "error": "Failed to fetch data from FHIR API",
            "source_url": endpoint,
        }

    return {
        "status": "success",
        "data": response_text,
        "error": None,
        "source_url": endpoint,
    }


def format_message_history(messages):
    lines = []
    for m in messages:
        role = m.type
        name = getattr(m, "name", None)
        prefix = f"{role}({name})" if name else role
        lines.append(f"{prefix}: {getattr(m, 'content', str(m))}")
    return "\n".join(lines)


def extract_latest_openapi_suggestion(messages):
    for msg in reversed(messages):
        if msg.content and re.search(r"\*\*Method\*\*:", msg.content):
            return msg.content
    return "No valid FHIR API suggestion found."


def fhir_prompt_from_state(state):
    openapi_suggestion = extract_latest_openapi_suggestion(state["messages"])
    full_message_history = format_message_history(state["messages"])
    return FHIR_AGENT_PROMPT_TEMPLATE.format(
        openapi_suggestion=openapi_suggestion, full_message_history=full_message_history
    )


fhir_agent = create_react_agent(
    name="fhir_agent",
    model=azure_foundry_gpt_4o,
    tools=[calling_fhir],
    prompt=fhir_prompt_from_state,
    checkpointer=memory,
    response_format=FHIRResponse,
)
