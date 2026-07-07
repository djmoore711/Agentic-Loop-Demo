"""
Requirement extraction from a JobDescription.

Two modes:
  - Mock: deterministic keyword matching against predefined dictionaries
  - Real: sends to LLM adapter for structured extraction

Returns structured JSON with required/preferred skills, tools, role signals,
and domain keywords.
"""

from __future__ import annotations

import json
from typing import Any

from llm_adapter import LLMAdapter
from models import JobDescription
from prompts import REQUIREMENT_EXTRACTION_PROMPT

# Predefined keyword dictionaries for mock-mode extraction
SKILL_DICTIONARIES: dict[str, list[str]] = {
    "programming": [
        "python", "go", "golang", "java", "rust", "javascript", "typescript",
        "bash", "shell", "powershell", "ruby", "c++", "scala",
    ],
    "cloud_infrastructure": [
        "aws", "gcp", "azure", "kubernetes", "gke", "eks", "aks",
        "docker", "terraform", "helm", "opa", "packer",
    ],
    "security_tools": [
        "siem", "splunk", "insightvm", "rapid7", "prisma cloud",
        "crowdstrike", "sentinelone", "qualys", "tenable", "wiz",
        "guardduty", "defender", "snort", "zeek",
    ],
    "vulnerability_management": [
        "vulnerability", "cve", "remediation", "patching",
        "scanning", "exploit", "insightvm", "qualys",
    ],
    "compliance": [
        "pci", "soc 2", "soc2", "iso 27001", "hipaa", "gdpr",
        "fedramp", "nist", "cis",
    ],
    "automation": [
        "automation", "automated", "scripting", "ci/cd", "pipeline",
        "soar", "orchestration", "workflow",
    ],
    "leadership": [
        "lead", "mentor", "manage", "cross-functional", "stakeholder",
        "team", "direct", "drive", "own",
    ],
}

ROLE_SIGNALS = ["senior", "staff", "principal", "lead", "manager", "director"]
DOMAIN_KEYWORDS = [
    "security", "cloud", "infrastructure", "automation", "detonation",
    "analysis", "triage", "incident", "response", "governance",
]


def analyze_mock(jd: JobDescription) -> dict[str, Any]:
    """Extract requirements using deterministic keyword matching."""
    text_lower = jd.raw_text.lower()

    required: list[dict[str, Any]] = []
    preferred: list[dict[str, Any]] = []
    tools: list[str] = []
    role_signals: list[str] = []
    domain_keywords: list[str] = []

    # Match skills
    for category, keywords in SKILL_DICTIONARIES.items():
        for kw in keywords:
            if kw in text_lower:
                importance = "required"
                evidence = f"Experience with {kw} in a professional or project context"
                entry = {
                    "name": kw.upper() if len(kw) <= 4 else kw.title(),
                    "category": category,
                    "importance": importance,
                    "evidence_needed": evidence,
                }
                if entry["name"] not in [r["name"] for r in required]:
                    required.append(entry)
                if category in ("security_tools", "vulnerability_management") and kw not in tools:
                    tools.append(entry["name"])

    # Match role signals
    for signal in ROLE_SIGNALS:
        if signal in text_lower:
            role_signals.append(signal)

    # Match domain keywords
    for kw in DOMAIN_KEYWORDS:
        if kw in text_lower and kw not in domain_keywords:
            domain_keywords.append(kw)

    # Try to extract title and company from first lines
    title = jd.title or ""
    company = jd.company or ""
    lines = jd.raw_text.strip().split("\n")
    if not title and lines:
        title = lines[0].strip()[:100]
    if not company and len(lines) > 1:
        # crude: look for "at [Company]" or second line
        for line in lines[:5]:
            if " at " in line.lower():
                parts = line.split(" at ")
                if len(parts) >= 2:
                    company = parts[-1].strip()[:100]
                    break

    return {
        "title": title,
        "company": company,
        "required": required,
        "preferred": preferred,
        "tools": tools,
        "role_signals": role_signals,
        "domain_keywords": domain_keywords,
    }


def analyze_real(jd: JobDescription, adapter: LLMAdapter) -> dict[str, Any]:
    """Extract requirements using a real LLM adapter."""
    prompt = REQUIREMENT_EXTRACTION_PROMPT.format(job_text=jd.raw_text)
    messages = [
        {"role": "system", "content": "You are a job description analyzer. Return strict JSON only."},
        {"role": "user", "content": prompt},
    ]
    response = adapter.complete(messages)
    text = response.text or ""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON from text
        import re

        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        # Fallback to mock if parsing fails
        return analyze_mock(jd)


def analyze(jd: JobDescription, adapter: LLMAdapter | None = None, mock: bool = True) -> dict[str, Any]:
    """Dispatch to mock or real analysis based on mode."""
    if mock or adapter is None:
        return analyze_mock(jd)
    return analyze_real(jd, adapter)
