"""
Tool functions for the resume agentic loop.

Each tool is a Python function that the agent (model or mock) can call.
The agentic loop dispatches tool calls to these functions via execute_tool().

These tools represent the agent's interface to the outside world:
  - query_experience: read from SQLite state
  - query_bullets: read from SQLite state
  - query_tools: read from SQLite state
  - store_experience: write to SQLite state
  - store_bullet: write to SQLite state
  - ask_user: interact with the human via CLI
  - generate_resume: produce the final artifact

Tool schemas are defined for both native tool calling and JSON fallback.
"""

from __future__ import annotations

import json
from typing import Any

import database
from models import ToolCall, ToolResult

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


def query_experience(query: str, category: str | None = None) -> ToolResult:
    """Search experience entries in the database."""
    rows = database.query_experience(query, category)
    return ToolResult(
        name="query_experience",
        result={"count": len(rows), "entries": rows},
        success=True,
    )


def query_bullets(company: str | None = None, keyword: str | None = None) -> ToolResult:
    """Search resume bullets in the database."""
    rows = database.query_bullets(company, keyword)
    return ToolResult(
        name="query_bullets",
        result={"count": len(rows), "bullets": rows},
        success=True,
    )


def query_tools(tool_name: str) -> ToolResult:
    """Search the tool inventory."""
    rows = database.query_tools(tool_name)
    return ToolResult(
        name="query_tools",
        result={"count": len(rows), "tools": rows},
        success=True,
    )


def store_experience(
    company: str,
    title: str,
    date_range: str,
    category: str,
    details: str,
) -> ToolResult:
    """Store a new experience entry in the database."""
    row_id = database.store_experience(company, title, date_range, category, details)
    return ToolResult(
        name="store_experience",
        result={"id": row_id, "message": f"Stored experience entry #{row_id}"},
        success=True,
    )


def store_bullet(
    experience_id: int | None,
    company: str,
    title: str,
    bullet_text: str,
) -> ToolResult:
    """Store a new resume bullet in the database."""
    row_id = database.store_bullet(experience_id, company, title, bullet_text)
    return ToolResult(
        name="store_bullet",
        result={"id": row_id, "message": f"Stored bullet #{row_id}"},
        success=True,
    )


def ask_user(question: str, reason: str = "") -> ToolResult:
    """Ask the user a question via CLI prompt.

    In non-interactive mode (e.g. mock demo), returns a fallback answer.
    """
    # Check if we're in interactive mode by looking for a global flag
    # set by the CLI dispatcher.
    interactive = getattr(ask_user, "_interactive", False)

    if not interactive:
        return ToolResult(
            name="ask_user",
            result={
                "answer": "[non-interactive: user clarification skipped in mock/demo mode]",
                "interactive": False,
            },
            success=True,
        )

    print(f"\n[Question] {question}")
    if reason:
        print(f"[Reason] {reason}")
    answer = input("> ").strip()
    return ToolResult(
        name="ask_user",
        result={"answer": answer, "interactive": True},
        success=True,
    )


def generate_resume(
    requirements: dict[str, Any],
    matched_experience: list[dict[str, Any]],
    user_profile: dict[str, Any] | None,
) -> ToolResult:
    """Generate a Markdown resume from evidence.

    This is a thin wrapper. The actual generation logic lives in generator.py.
    """
    # Import here to avoid circular dependency
    from generator import generate_markdown_resume

    bullets = database.query_bullets()
    certs = database.get_certifications()
    markdown = generate_markdown_resume(
        requirements=requirements,
        experience=matched_experience,
        bullets=bullets,
        profile=user_profile or {},
        certifications=certs,
    )
    return ToolResult(
        name="generate_resume",
        result={"resume_markdown": markdown},
        success=True,
    )


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------

TOOL_FUNCTIONS = {
    "query_experience": query_experience,
    "query_bullets": query_bullets,
    "query_tools": query_tools,
    "store_experience": store_experience,
    "store_bullet": store_bullet,
    "ask_user": ask_user,
    "generate_resume": generate_resume,
}


def execute_tool(tool_call: ToolCall) -> ToolResult:
    """Dispatch a ToolCall to the matching function and return its ToolResult."""
    fn = TOOL_FUNCTIONS.get(tool_call.name)
    if fn is None:
        return ToolResult(
            name=tool_call.name,
            result={"error": f"Unknown tool: {tool_call.name}"},
            success=False,
        )
    try:
        return fn(**tool_call.arguments)
    except TypeError as e:
        return ToolResult(
            name=tool_call.name,
            result={"error": f"Invalid arguments for {tool_call.name}: {e}"},
            success=False,
        )
    except Exception as e:
        return ToolResult(
            name=tool_call.name,
            result={"error": f"Tool execution failed: {e}"},
            success=False,
        )


# ---------------------------------------------------------------------------
# Tool schemas (for native tool calling and JSON fallback)
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "name": "query_experience",
        "description": "Search the experience database for entries matching a query string. Optionally filter by category.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term (company, title, keyword in details)"},
                "category": {"type": "string", "description": "Optional category filter (e.g. security_automation, cloud_security)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "query_bullets",
        "description": "Search resume bullets by optional company name and/or keyword.",
        "parameters": {
            "type": "object",
            "properties": {
                "company": {"type": "string", "description": "Company name to filter by"},
                "keyword": {"type": "string", "description": "Keyword to search in bullet text"},
            },
            "required": [],
        },
    },
    {
        "name": "query_tools",
        "description": "Search the tool inventory by tool name.",
        "parameters": {
            "type": "object",
            "properties": {
                "tool_name": {"type": "string", "description": "Tool name to search for"},
            },
            "required": ["tool_name"],
        },
    },
    {
        "name": "store_experience",
        "description": "Store a new experience entry in the database.",
        "parameters": {
            "type": "object",
            "properties": {
                "company": {"type": "string"},
                "title": {"type": "string"},
                "date_range": {"type": "string"},
                "category": {"type": "string"},
                "details": {"type": "string"},
            },
            "required": ["company", "title", "date_range", "category", "details"],
        },
    },
    {
        "name": "store_bullet",
        "description": "Store a new resume bullet in the database.",
        "parameters": {
            "type": "object",
            "properties": {
                "experience_id": {"type": "integer", "description": "ID of the parent experience entry"},
                "company": {"type": "string"},
                "title": {"type": "string"},
                "bullet_text": {"type": "string"},
            },
            "required": ["company", "title", "bullet_text"],
        },
    },
    {
        "name": "ask_user",
        "description": "Ask the user a clarifying question. Use when evidence is missing for a job requirement.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The question to ask"},
                "reason": {"type": "string", "description": "Why this question matters"},
            },
            "required": ["question"],
        },
    },
    {
        "name": "generate_resume",
        "description": "Generate the final Markdown resume from matched evidence, user profile, and job requirements.",
        "parameters": {
            "type": "object",
            "properties": {
                "requirements": {"type": "object", "description": "Extracted job requirements"},
                "matched_experience": {"type": "array", "description": "Experience entries matched from DB"},
                "user_profile": {"type": "object", "description": "User profile from DB"},
            },
            "required": ["requirements", "matched_experience"],
        },
    },
]


def tool_result_to_json(result: ToolResult) -> str:
    """Serialize a ToolResult to JSON for feeding back into the loop."""
    return json.dumps(
        {"name": result.name, "result": result.result, "success": result.success},
        default=str,
    )
