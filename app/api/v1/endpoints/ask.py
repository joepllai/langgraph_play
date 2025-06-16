from app.api.v1.router import router

from app.api.v1.models.ask import QuestionData
from app.agent.fhir_agent import fhir_agent


@router.post("/ask")
async def ask(
    data: QuestionData,
):
    response = fhir_agent.invoke(
        input={
            "messages": [
                {
                    "role": "user",
                    "content": data.query,
                }
            ],
        },
        config={"thread_id": data.session_id},
    )
    return response["structured_response"]
