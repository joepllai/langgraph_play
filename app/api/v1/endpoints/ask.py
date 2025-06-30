from langfuse import observe
from langfuse.langchain import CallbackHandler
from typing import cast
from langchain_core.runnables import RunnableConfig

from app.api.v1.router import router
from app.api.v1.models.ask import QuestionData
from app.agent.supervisor_agent import supervisor_agent


@observe
@router.post("/ask")
async def ask(
    data: QuestionData,
):
    config = cast(RunnableConfig, {
        "thread_id": data.session_id,
        "callbacks": [CallbackHandler()],
    })
    response = await supervisor_agent.ainvoke(
        input={
            "messages": [
                {
                    "role": "user",
                    "content": data.query,
                }
            ],
        },
        config=config,
    )
    return response["structured_response"]
