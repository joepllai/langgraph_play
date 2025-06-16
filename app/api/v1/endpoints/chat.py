from app.api.v1.router import router

from app.api.v1.models.chat import QuestionData
from app.agent.fhir_agent import fhir_agent


@router.post("/ask")
async def ask(
    data: QuestionData,
):
    response = fhir_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": data.query,
                }
            ]
        }
    )
    return response["structured_response"]
