# Agent Toolbelt Framework

![Tests](https://github.com/simonharris/agent_toolbelt/actions/workflows/test.yml/badge.svg)

A minimal Python framework for registering, managing, and invoking tool functions for LLM (Large Language Model) interactions and agentic AI.

## Features
- Singleton tool registry for dynamic function registration and lookup
- Decorator for easy tool registration
- Automatic metadata generation for tool functions (for LLM tool use)
- Unified tool invocation interface with argument parsing
- Custom exception for missing tools
- Type hints throughout for clarity and static analysis
- Unit tests and linting included

## Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/simonharris/agent_toolbelt.git
   cd agent_toolbelt
   ```
2. Create a virtual environment and install dependencies:
   ```sh
   make install
   ```

## Usage

### Registering a Tool
```python
from framework import register_tool

@register_tool('add')
def add(a: str, b: str) -> str:
    """Add two numbers as strings and return the sum as a string."""
    return str(int(a) + int(b))
```

### Running a Tool
```python
from framework import run_tool
import json

result = run_tool({
    "name": "add",
    "arguments": json.dumps({"a": "2", "b": "3"})
})
print(result)  # Output: '5'
```


### Generating Tool Metadata
```python
from framework import generate_tool_metadata, TOOL_REGISTRY
meta = generate_tool_metadata(TOOL_REGISTRY['add'])
print(meta)
```

### Integrating with an LLM Call
You can use the generated tool metadata as part of your LLM API call (e.g., OpenAI, Anthropic, etc.).

```python
# Example: Using with OpenAI's chat API
from framework import get_tools

tools = get_tools()  # List of tool metadata dicts

response = client.chat.completions.create(
  model=MODEL,
  messages=messages,
  tools=tools,  # Pass the tool metadata here
  tool_choice="auto"
)
```
This allows the LLM to see and use your registered tools automatically during the conversation.

## Testing
Run all tests with:
```sh
make test
```

## Linting & Code Quality
- Check PEP8/style issues:
  ```sh
  make lint
  ```
- See a code quality score:
  ```sh
  make pylint
  ```

## License
MIT
