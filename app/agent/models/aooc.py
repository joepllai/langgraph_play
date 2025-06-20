from __future__ import annotations
from typing import Sequence, Any, Callable, Union, Optional
import time, httpx, threading, json
from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration

AUTH_URL = "https://aoccaihub.asus.com/aoccgpt2/v1/openapi/auth"
CHAT_URL = "https://aoccaihub.asus.com/aoccgpt2/v1/openapi/chat"
NEW_URL  = "https://aoccaihub.asus.com/aoccgpt2/v1/openapi/new_session"

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

    def serialize_content(self, content):
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            new_blocks = []
            for block in content:
                if isinstance(block, dict):
                    # Ensure 'type' exists in each block
                    if "type" not in block:
                        block = {**block, "type": "text"}
                    new_blocks.append(block)
                else:
                    # If it's a string, wrap as a text block
                    new_blocks.append({"type": "text", "text": block})
            return new_blocks
        else:
            return str(content)

    def serialize_message(self, m):
        base = {
            "role": (
                "user" if m.type == "human"
                else "assistant" if m.type == "ai"
                else m.type
            ),
            "content": self.serialize_content(m.content),
            "type": m.type,
        }
        # Optionally include extra fields if present
        if hasattr(m, "name"):
            base["name"] = getattr(m, "name", None)
        if hasattr(m, "tool_call_id"):
            base["tool_call_id"] = getattr(m, "tool_call_id", None)
        if hasattr(m, "additional_kwargs"):
            base["additional_kwargs"] = getattr(m, "additional_kwargs", {})
        if hasattr(m, "response_metadata"):
            base["response_metadata"] = getattr(m, "response_metadata", {})
        if hasattr(m, "tool_calls"):
            base["tool_calls"] = getattr(m, "tool_calls", None)
        if hasattr(m, "usage_metadata"):
            base["usage_metadata"] = getattr(m, "usage_metadata", None)
        return base
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
        messages: list[HumanMessage | AIMessage | ToolMessage | SystemMessage],
        stop: list[str] | None = None,
        **kwargs
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
            "message": [m.model_dump() for m in messages],
        }

        r = httpx.post(
            CHAT_URL,
            headers={"Authorization": token},
            json=payload,
            timeout=self._timeout,
        )
        r.raise_for_status()
        js = r.text
        if "textResponse" not in js:
            print("[DEBUG] API response:", js)
            raise KeyError("'textResponse' not in API response")
        content = js["textResponse"]

        # --- Tool-calling simulation ---
        # If the model outputs TOOL_CALL: {...}, parse and return as tool_call
        if content.strip().startswith("TOOL_CALL:"):
            try:
                tool_call_json = content.strip()[len("TOOL_CALL:"):].strip()
                tool_call = json.loads(tool_call_json)
                tool_calls = [{
                    "id": "tool_call_1",
                    "name": tool_call["name"],
                    "arguments": tool_call.get("arguments", {}),
                    "type": "function"
                }]
                return ChatResult(
                    generations=[
                        ChatGeneration(
                            message=AIMessage(
                                content="",
                                additional_kwargs={"tool_calls": tool_calls}
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