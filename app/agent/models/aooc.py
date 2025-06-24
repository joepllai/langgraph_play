from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Sequence, Any, Callable, Union, Optional
import time, httpx, threading, json
from langchain_core.tools import BaseTool
from langchain_core.output_parsers.openai_tools import PydanticToolsParser
from langchain_core.runnables import RunnableMap, RunnablePassthrough
from langchain_core.language_models import BaseChatModel
from langchain_core.callbacks import CallbackManagerForLLMRun

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    ToolMessage,
    SystemMessage,
    BaseMessage,
)
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.output_parsers import PydanticOutputParser

AUTH_URL = "https://aoccaihub.asus.com/aoccgpt2/v1/openapi/auth"
CHAT_URL = "https://aoccaihub.asus.com/aoccgpt2/v1/openapi/chat"
NEW_URL = "https://aoccaihub.asus.com/aoccgpt2/v1/openapi/new_session"


class AsusAOCGPT(BaseChatModel):
    """Minimal LangChain wrapper for ASUS AOCC GPT service."""

    def __init__(
        self,
        api_key: str,
        assistant_id: str | None = "",
        service: str = "azure",
        version: str = "gpt4o",
        timeout: int = 45,
    ):
        super().__init__()
        self._api_key = api_key
        self._assistant_id = assistant_id
        self._service = service
        self._version = version
        self._timeout = timeout

        self._token_lock = threading.Lock()
        self._token_expire_at = 0
        self._token: str | None = None

    # -------------- LangChain 接口實作 ------------------
    @property
    def _llm_type(self) -> str:
        return "asus-aoc-gpt"

    def flatten_chat_messages_to_prompt(self, messages: list[BaseMessage]) -> str:
        prompt = ""
        for message in messages:
            if message.type == "system":
                prompt += f"[System] {message.content}\n\n"
            elif message.type == "human":
                prompt += f"[User] {message.content}\n\n"
            elif message.type == "ai":
                prompt += f"[Assistant] {message.content}\n\n"
            else:
                prompt += f"[{message.type}] {message.content}\n\n"
        return prompt.strip()

    def _get_token(self) -> str:
        with self._token_lock:
            if self._token and time.time() < self._token_expire_at - 60:
                return self._token
            # 重新取得
            r = httpx.get(
                AUTH_URL,
                headers={"Authorization": self._api_key},
                timeout=self._timeout,
            )
            r.raise_for_status()
            js = r.json()
            self._token = js["token"]
            # 官方沒回 expires_in？假設 30 分鐘
            self._token_expire_at = time.time() + js.get("expires_in", 1800)
            return self._token

    def _new_session(self, token: str) -> str:
        r = httpx.post(
            NEW_URL,
            headers={"Authorization": token},
            timeout=self._timeout,
        )
        r.raise_for_status()
        return r.json()["session_id"]

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs,
    ) -> ChatResult:
        # stop and kwargs are required by interface but unused
        token = self._get_token()
        session_id = self._new_session(token)
        payload = {
            "session_id": session_id,
            "response_type": "normal",
            "assistant_id": self._assistant_id,
            "service": self._service,
            "version": self._version,
            "message": self.flatten_chat_messages_to_prompt(messages),
        }

        r = httpx.post(
            CHAT_URL,
            headers={"Authorization": token},
            json=payload,
            timeout=self._timeout,
        )
        r.raise_for_status()
        js = r.json()
        if "textResponse" not in js:
            print("[DEBUG] API response:", js)
            raise KeyError("'textResponse' not in API response")
        content = js["textResponse"]

        # --- Tool-calling simulation ---
        # If the model outputs TOOL_CALL: {...}, parse and return as tool_call
        if content.strip().startswith("TOOL_CALL:"):
            try:
                tool_call_json = content.strip()[len("TOOL_CALL:") :].strip()
                tool_call = json.loads(tool_call_json)
                tool_calls = [
                    {
                        "id": "tool_call_1",
                        "name": tool_call["name"],
                        "arguments": tool_call.get("arguments", {}),
                        "type": "function",
                    }
                ]
                return ChatResult(
                    generations=[
                        ChatGeneration(
                            message=AIMessage(
                                content="", additional_kwargs={"tool_calls": tool_calls}
                            )
                        )
                    ]
                )
            except Exception as e:
                print("[DEBUG] Tool call parsing failed:", e)
                # fallback to normal message

        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=content))]
        )

    def bind_tools(
        self,
        tools: Sequence[Union[dict, type, Callable, BaseTool]],
        *,
        tool_choice: Optional[Union[str]] = None,
        **kwargs: Any,
    ):
        self._tools = tools
        self._tool_choice = tool_choice
        return self

    # def with_structured_response(
    #     self,
    #     schema: Union[dict, type],
    #     include_raw: bool = False,
    #     **kwargs: Any,
    # ) -> RunnableMap:
    #     """Configure the model to return structured responses."""
    #     if isinstance(schema, type) and issubclass(schema, BaseModel):
    #         output_parser = PydanticToolsParser(tools=[schema], first_tool_only=True)
    #     else:
    #         raise ValueError("Unsupported schema type. Use Pydantic models.")

    #     llm = self.bind_tools(
    #         [schema],
    #         tool_choice="any",
    #         ls_structured_output_format={
    #             "kwargs": {"method": "function_calling"},
    #             "schema": schema,
    #         },
    #     )

    #     if include_raw:
    #         parser_assign = RunnablePassthrough.assign(
    #             parsed=lambda raw: output_parser.parse(raw),
    #             parsing_error=lambda _: None,
    #         )
    #         parser_none = RunnablePassthrough.assign(parsed=lambda _: None)
    #         parser_with_fallback = parser_assign.with_fallbacks(
    #             [parser_none], exception_key="parsing_error"
    #         )
    #         return RunnableMap(raw=llm) | parser_with_fallback
