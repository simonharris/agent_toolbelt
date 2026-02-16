import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from framework import TOOL_REGISTRY, register_tool, run_tool, generate_tool_metadata, get_tools, ToolNotFoundError
import pytest
import json

def test_register_and_run_tool():
	@register_tool('add')
	def add(a: str, b: str) -> str:
		"""Add two numbers as strings and return the sum as a string."""
		return str(int(a) + int(b))

	tool_call = {
		"name": "add",
		"arguments": json.dumps({"a": "2", "b": "3"})
	}
	result = run_tool(tool_call)
	assert result == "5"

def test_tool_not_found():
	tool_call = {"name": "nonexistent", "arguments": json.dumps({})}
	with pytest.raises(ToolNotFoundError):
		run_tool(tool_call)

def test_generate_tool_metadata():
	@register_tool('echo')
	def echo(msg: str) -> str:
		"""Echo the input message."""
		return msg
	meta = generate_tool_metadata(TOOL_REGISTRY['echo'])
	assert meta["name"] == "echo"
	assert "parameters" in meta
	assert "msg" in meta["parameters"]["properties"]

def test_get_tools():
	tools = get_tools()
	assert isinstance(tools, list)
	assert any(tool["function"]["name"] == "echo" for tool in tools)
