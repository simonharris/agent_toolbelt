import inspect
import json
from typing import Any, Callable, Dict, Optional, TypeVar, List
from collections.abc import ValuesView, ItemsView, KeysView, Iterator


class ToolNotFoundError(Exception):
    """Exception raised when a tool is not found in the registry."""
    pass


T = TypeVar('T', bound=Callable)

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

