from collections.abc import ValuesView, ItemsView, KeysView, Iterator
import inspect
import json
import os
from typing import Any, Callable, Dict, Optional, TypeVar, List

from openai import OpenAI


T = TypeVar('T', bound=Callable)

class ToolNotFoundError(Exception):
    """Exception raised when a tool is not found in the registry."""
    pass


class ToolRegistry:
    _instance: Optional['ToolRegistry'] = None
    _tools: Dict[str, Callable[..., Any]] = {}

    def __new__(cls) -> 'ToolRegistry':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __getitem__(self, key: str) -> Callable[..., Any]:
        return self._tools[key]

    def __setitem__(self, key: str, value: Callable[..., Any]) -> None:
        self._tools[key] = value

    def __delitem__(self, key: str) -> None:
        del self._tools[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._tools)

    def values(self) -> ValuesView[Callable[..., Any]]:
        return self._tools.values()

    def items(self) -> ItemsView[str, Callable[..., Any]]:
        return self._tools.items()

    def keys(self) -> KeysView[str]:
        return self._tools.keys()

    def get(self, key: str, default: Optional[Callable[..., Any]] = None) -> Optional[Callable[..., Any]]:
        return self._tools.get(key, default)

    def __contains__(self, key: str) -> bool:
        return key in self._tools


TOOL_REGISTRY: ToolRegistry = ToolRegistry()


def register_tool(name: str) -> Callable[[T], T]:
    """Decorator to register a function as a tool."""
    def wrapper(fn: T) -> T:
        TOOL_REGISTRY[name] = fn
        return fn
    return wrapper


def generate_tool_metadata(tool_fn: Callable[..., Any]) -> dict:
    """
    Generate a tool function description dictionary from a function object.
    The dictionary will have keys: name, description, parameters (type, properties, required, additionalProperties).
    """
    sig = inspect.signature(tool_fn)
    name = tool_fn.__name__
    description = inspect.getdoc(tool_fn) or f"Tool function: {name}"
    properties: dict[str, dict[str, str]] = {}
    required: List[str] = []
    for param in sig.parameters.values():
        properties[param.name] = {
            "type": "string",  # Default to string; could be improved with type hints
            "description": f"Parameter: {param.name}"
        }
        required.append(param.name)
    return {
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False
        }
    }


def run_tool(tool_call: dict) -> Any:
    name: str = tool_call["name"]
    args: dict = json.loads(tool_call["arguments"])
    tool_fn = TOOL_REGISTRY.get(name)
    if not tool_fn:
        raise ToolNotFoundError(f"Unknown tool: {name}")
    result = tool_fn(**args)
    return result


def get_tools() -> list[dict]:
    return [
        {"type": "function", "function": generate_tool_metadata(fn)}
        for fn in TOOL_REGISTRY.values()
    ]


class Chatter:
    """Chatter class encapsulates the chat logic, including message formatting,
    tool call handling, and interaction with the OpenAI client."""

    def __init__(self, system_message=None, tools=None, client=None, model=None):
        self.system_message = system_message or "You are a helpful assistant."
        self.tools = tools if tools is not None else get_tools()
        self.client = client or OpenAI()
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5-nano")

    def _handle_tool_calls(self, message) -> list:
        """
        Runs all tool calls in the message and returns OpenAI-compatible tool response dicts.
        May raise ToolNotFoundError if a tool is not found.
        """
        responses = []
        for tool_call in message.tool_calls:
            result = run_tool({
                "name": tool_call.function.name,
                "arguments": tool_call.function.arguments
            })
            responses.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "content": json.dumps(result),
            })
        return responses

    def chat(self, message: str, history: list) -> str:
        history.append({"role": "user", "content": message})

        def to_openai_message(msg):
            if msg["role"] == "system":
                return {"role": "system", "content": msg["content"]}
            elif msg["role"] == "user":
                return {"role": "user", "content": msg["content"]}
            elif msg["role"] == "assistant":
                m = {"role": "assistant", "content": msg["content"]}
                if "tool_calls" in msg and msg["tool_calls"]:
                    m["tool_calls"] = msg["tool_calls"]
                return m
            elif msg["role"] == "tool":
                return {
                    "role": "tool",
                    "tool_call_id": msg["tool_call_id"],
                    "name": msg["name"],
                    "content": msg["content"]
                }
            else:
                raise ValueError(f"Invalid role in message: {msg}")

        messages = [{"role": "system", "content": self.system_message}] + [to_openai_message(m) for m in history]

        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            assistant_message = response.choices[0].message

            tool_calls = getattr(assistant_message, "tool_calls", None)
            if tool_calls:
                tool_calls = [tc.to_dict() if hasattr(tc, "to_dict") else dict(tc) for tc in tool_calls]
                history.append({"role": "assistant", "content": assistant_message.content or "Tool call issued.", "tool_calls": tool_calls})
                tool_results = self._handle_tool_calls(assistant_message)
                for tool_msg in tool_results:
                    content = tool_msg["content"] or "No results found."
                    history.append({
                        "role": "tool",
                        "tool_call_id": tool_msg["tool_call_id"],
                        "name": tool_msg["name"],
                        "content": content
                    })
                messages = [{"role": "system", "content": self.system_message}] + [to_openai_message(m) for m in history]
                continue
            content = assistant_message.content or "No response."
            history.append({"role": "assistant", "content": content})
            return content
