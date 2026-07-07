"""
Data models for the resume agentic loop.

These Pydantic models define the structured data passed between the
agentic loop, tools, and the database layer.

This module has no project-specific or personal data dependencies.
It is intentionally generic and reusable.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class JobDescription(BaseModel):
    """Structured representation of a parsed job description."""

    title: str = Field(default="", description="Job title, if extractable")
    company: str = Field(default="", description="Hiring company, if extractable")
    location: str = Field(default="", description="Job location, if listed")
    raw_text: str = Field(..., description="Raw job description text")
    source_url: str = Field(default="", description="Source URL if fetched from web")
    extraction_method: str = Field(
        default="file",
        description="How the text was obtained: file, text, url-jsonld, url-meta, url-body",
    )
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class ExperienceEntry(BaseModel):
    """A single professional experience entry."""

    company: str
    title: str
    date_range: str = Field(default="[DATE RANGE NEEDED]")
    category: str = Field(default="general")
    details: str = Field(default="")
    source_confirmed: bool = Field(default=False)


class ResumeDraft(BaseModel):
    """A generated resume draft."""

    name: str = Field(default="[Name Needed]")
    headline: str = Field(default="")
    summary: str = Field(default="")
    skills: list[str] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)


class ToolCall(BaseModel):
    """A tool call requested by the agent."""

    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """The result of executing a tool call."""

    name: str
    result: Any
    success: bool = True
