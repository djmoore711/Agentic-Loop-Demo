"""Tests for tools.py — tool dispatch and error handling."""

import pytest
from models import ToolCall, ToolResult
from tools import execute_tool, ask_user, tool_result_to_json


class TestExecuteTool:
    """execute_tool dispatches ToolCall to registered tool functions."""

    def test_unknown_tool_returns_error(self):
        result = execute_tool(ToolCall(name="nonexistent_tool", arguments={}))
        assert result.success is False
        assert "Unknown tool" in str(result.result)

    def test_type_mismatch_returns_error(self):
        """Calling a tool with wrong arg types (int where str expected) should be caught."""
        result = execute_tool(ToolCall(name="query_experience", arguments={"query": 42}))
        # query=42 fails when query.lower() is called — database.py expects str
        assert result.success is False

    def test_missing_required_args_returns_error(self):
        """query_experience requires 'query' — omit it."""
        result = execute_tool(ToolCall(name="query_experience", arguments={}))
        assert result.success is False
        assert "Invalid arguments" in str(result.result) or "TypeError" in str(result.result) or "missing" in str(result.result).lower()

    def test_dispatch_basic_tool(self):
        """query_tools with a valid tool name returns results."""
        result = execute_tool(ToolCall(name="query_tools", arguments={"tool_name": "Python"}))
        assert result.success is True
        assert "count" in result.result
        assert "tools" in result.result


class TestAskUser:
    """ask_user handles interactive/non-interactive modes."""

    def test_non_interactive_returns_fallback(self):
        ask_user._interactive = False
        result = ask_user(question="Test question?")
        assert result.success is True
        assert "non-interactive" in result.result["answer"]
        assert result.result["interactive"] is False

    def test_interactive_flag_respected(self):
        ask_user._interactive = True
        # Can't actually test interactive stdin here, just verify the flag pathway
        pass


class TestToolResultToJson:
    """tool_result_to_json serializes ToolResult to JSON string."""

    def test_success_result(self):
        result = ToolResult(name="test", result={"key": "value"}, success=True)
        json_str = tool_result_to_json(result)
        assert '"name": "test"' in json_str
        assert '"success": true' in json_str

    def test_error_result(self):
        result = ToolResult(name="test", result={"error": "something failed"}, success=False)
        json_str = tool_result_to_json(result)
        assert '"success": false' in json_str
        assert '"error"' in json_str
