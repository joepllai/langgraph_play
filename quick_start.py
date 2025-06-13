import requests
import os
from pydantic import BaseModel
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from prompts.agent_prompts.fhir_agent import FHIR_AGENT_PROMPTS


class FHIRResponse(BaseModel):
    answer: str


load_dotenv()

llm = init_chat_model(
    model="gemini-2.5-flash-preview-05-20",
    model_provider="google_genai",
    temperature=0,
)


def calling_fhir(params: dict) -> dict:
    """
    Make an HTTP GET request to the FHIR API endpoint.

    Args:
        params (dict): A dictionary containing FHIR query parameters
            - resource_type (str): The FHIR resource type 
                (e.g., 'Patient', 'Observation')
            - resource_id (str, optional): The specific resource ID
            - query_params (dict, optional): Additional query parameters

    Returns:
        dict: A dictionary containing the status and data of the response
            - status: "success" or "error"
            - data: The JSON response data if successful, None if failed
            - error: Error message if the request failed
    """
    print("Calling FHIR API with params:", params)
    try:
        # Construct the base URL
        base_url = "https://hapi.35.229.200.151.nip.io/fhir/CP_V3"

        # Build the resource path
        resource_path = params.get("resource_type", "")
        if resource_id := params.get("resource_id"):
            resource_path = f"{resource_path}/{resource_id}"

        # Construct the full URL
        url = f"{base_url}/{resource_path}"

        # Add query parameters if they exist
        query_params = params.get("query_params", {})

        response = requests.get(
            url,
            params=query_params,
            headers={
                "X-API-KEY": os.getenv("X-API-KEY"),
            },
            timeout=10
        )
        print("Response status code:", response.status_code)
        print("Response headers:", response.headers)
        print("Response content:", response.json())
        response.raise_for_status()
        return {"status": "success", "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "data": None, "error": str(e)}


fhir_agent = create_react_agent(
    model=llm,
    tools=[calling_fhir],
    response_format=FHIRResponse,
    prompt=FHIR_AGENT_PROMPTS
)

response = fhir_agent.invoke(
    {"messages": [
        {"role": "user", "content": "can you give me how many patients are there in the system start from 2025-01-01?"}]}
)

print(response["structured_response"])
