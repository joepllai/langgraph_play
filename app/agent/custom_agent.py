from typing import Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


llm = init_chat_model(
    model="gemini-2.5-flash-preview-05-20",
    model_provider="google_genai",
    temperature=0,
)


class MessageClassifier(BaseModel):
    message_type: Literal["emotional", "logical"] | None = Field(
        ...,
        description=(
            "Classify if the message requires an emotional or logical response"
        ),
    )


class State(TypedDict):
    messages: Annotated[list, add_messages]
    message_type: str | None
    next: str | None


def classify_message(state: State):
    last_message = state["messages"][-1]
    classifier_llm = llm.with_structured_output(MessageClassifier)

    result = classifier_llm.invoke(
        [
            {
                "role": "system",
                "content": "Classify the message as either 'emotional' or 'logical'. ",
            },
            {"role": "user", "content": last_message.content},
        ]
    )
    return {
        "message_type": result.message_type,
    }


def router(state: State) -> str:
    """
    Route the message to the appropriate agent or tool based
    on the message type and content.
    """
    message_type = state.get("message_type", "logical")

    # Default routing based on message type
    if message_type == "emotional":
        return {"next": "emotional_agent"}
    return {"next": "logical_agent"}


def emotional_agent(state: State) -> str:
    last_message = state["messages"][-1]
    messages = [
        {
            "role": "system",
            "content": "You are an emotional agent. Respond to the user's message with empathy and understanding.",
        },
        {"role": "user", "content": last_message.content},
    ]
    reply = llm.invoke(messages)
    return {"messages": [{"role": "assistant", "content": reply.content}]}


def logical_agent(state: State) -> str:
    last_message = state["messages"][-1]
    messages = [
        {
            "role": "system",
            "content": "You are a logical agent. Respond to the user's message with facts and reasoning.",
        },
        {"role": "user", "content": last_message.content},
    ]
    reply = llm.invoke(messages)
    return {"messages": [{"role": "assistant", "content": reply.content}]}


graph_builder = StateGraph(State)

graph_builder.add_node("classifier", classify_message)
graph_builder.add_node("router", router)
graph_builder.add_node("emotional_agent", emotional_agent)
graph_builder.add_node("logical_agent", logical_agent)

graph_builder.add_edge(START, "classifier")
graph_builder.add_edge("classifier", "router")
graph_builder.add_conditional_edges(
    "router",
    lambda state: state.get("next"),
    {
        "logical_agent": "logical_agent",
        "emotional_agent": "emotional_agent",
    },
)

graph_builder.add_edge("emotional_agent", END)
graph_builder.add_edge("logical_agent", END)


graph = graph_builder.compile()


def run_chatbot():
    state = {"messages": [], "message_type": None}
    while True:
        user_input = input("Message: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        state["messages"].append({"role": "user", "content": user_input})
        state = graph.invoke(state)
        if state["messages"]:
            print(f"Bot: {state['messages'][-1].content}")
