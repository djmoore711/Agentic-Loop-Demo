"""Tests for llm_adapter.py — MockAdapter state machine."""

import pytest
from llm_adapter import MockAdapter, get_adapter


class TestMockAdapter:
    """MockAdapter follows a deterministic sequence of tool calls and decisions."""

    def test_initial_step_queries_tools(self):
        adapter = MockAdapter()
        response = adapter.complete(messages=[], tools=[])
        assert response.stop_reason == "tool_use"
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "query_tools"
        assert response.tool_calls[0].arguments["tool_name"] == "Python"

    def test_step_1_queries_experience(self):
        adapter = MockAdapter()
        # step 0
        adapter.complete(messages=[], tools=[])
        # step 1
        response = adapter.complete(messages=[], tools=[])
        assert response.stop_reason == "tool_use"
        assert response.tool_calls[0].name == "query_experience"

    def test_step_2_queries_bullets(self):
        adapter = MockAdapter()
        for _ in range(2):  # steps 0, 1
            adapter.complete(messages=[], tools=[])
        response = adapter.complete(messages=[], tools=[])  # step 2
        assert response.stop_reason == "tool_use"
        assert response.tool_calls[0].name == "query_bullets"

    def test_step_3_asks_user(self):
        adapter = MockAdapter()
        for _ in range(3):  # steps 0, 1, 2
            adapter.complete(messages=[], tools=[])
        response = adapter.complete(messages=[], tools=[])  # step 3
        assert response.stop_reason == "needs_user_input"
        assert len(response.questions) == 2

    def test_step_4_stores_experience(self):
        adapter = MockAdapter()
        for _ in range(4):  # steps 0, 1, 2, 3
            adapter.complete(messages=[], tools=[])
        response = adapter.complete(messages=[], tools=[])  # step 4
        assert response.stop_reason == "tool_use"
        assert response.tool_calls[0].name == "store_experience"

    def test_final_step_returns_resume(self):
        adapter = MockAdapter()
        for _ in range(6):
            adapter.complete(messages=[], tools=[])
        response = adapter.complete(messages=[], tools=[])
        assert response.stop_reason == "final_resume"

    def test_get_adapter_returns_mock(self):
        adapter = get_adapter()
        assert isinstance(adapter, MockAdapter)

    def test_adapter_cycles_beyond_final(self):
        """After the final step, remaining steps also return final_resume."""
        adapter = MockAdapter()
        for _ in range(7):
            adapter.complete(messages=[], tools=[])
        response = adapter.complete(messages=[], tools=[])
        assert response.stop_reason == "final_resume"
