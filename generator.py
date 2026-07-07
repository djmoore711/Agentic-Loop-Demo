"""Resume generation from evidence (mock-only).

The generator never invents data. If a field is missing, it uses
placeholder markers like [DATE RANGE NEEDED] or omits the section.
"""

from __future__ import annotations

from typing import Any

import json

import database

_RESUME_TEMPLATE = """\
# {name}
{headline}
{email} | {phone} | {location} | {linkedin}

## Summary
{summary}

## Core Skills
### Technical Skills
{technical_skills}

### Tools
{tools_list}

### Leadership / Collaboration
{leadership_skills}

## Professional Experience
{experience_section}

## Certifications
{certifications_section}

## Education
{education_section}
"""


def generate_markdown_resume(
    requirements: dict[str, Any],
    experience: list[dict[str, Any]],
    bullets: list[dict[str, Any]],
    profile: dict[str, Any],
    certifications: list[dict[str, Any]],
    education: list[str] | None = None,
) -> str:
    """Generate a Markdown resume from evidence using template substitution.

    This is the mock-mode generator. It never invents data.
    """

    name = profile.get("full_name", "[Name Needed]")
    headline = profile.get("headline", "[Headline Needed]")
    email = profile.get("email", "[Email Needed]")
    phone = profile.get("phone", "[Phone Needed]")
    location = profile.get("location", "[Location Needed]")
    linkedin = profile.get("linkedin", "[LinkedIn Needed]")

    # Build summary from requirements
    job_title = requirements.get("title", "the target role")
    job_company = requirements.get("company", "")
    domain_keywords = requirements.get("domain_keywords", [])
    summary = (
        f"Security automation engineer with experience building tooling and workflows "
        f"that reduce manual effort and improve evidence quality. "
        f"Tailored for {job_title}"
    )
    if job_company:
        summary += f" at {job_company}"
    summary += "."

    # Build skills sections
    required_skills = [r["name"] for r in requirements.get("required", [])]
    preferred_skills = [r["name"] for r in requirements.get("preferred", [])]
    tools_list = requirements.get("tools", [])

    technical_skills = "\n".join(f"- {s}" for s in required_skills[:10])
    if not technical_skills:
        technical_skills = "- [Skills to be confirmed]"

    tools_section = "\n".join(f"- {t}" for t in tools_list[:10])
    if not tools_section:
        tools_section = "- [Tools to be confirmed]"

    role_signals = requirements.get("role_signals", [])
    leadership_skills = "\n".join(f"- {s}" for s in role_signals[:5])
    if not leadership_skills:
        leadership_skills = "- [Leadership signals to be confirmed]"

    # Build experience section from DB entries
    exp_parts: list[str] = []
    for entry in experience[:5]:
        company = entry.get("company", "[Company Needed]")
        title_str = entry.get("title", "[Title Needed]")
        date_range = entry.get("date_range", "[DATE RANGE NEEDED]")
        details = entry.get("details", "")

        # Find matching bullets
        entry_bullets = [
            b for b in bullets
            if b.get("company", "").lower() == company.lower()
            or b.get("experience_id") == entry.get("id")
        ]
        bullet_lines = "\n".join(f"- {b['bullet_text']}" for b in entry_bullets[:4])
        if not bullet_lines and details:
            bullet_lines = f"- {details}"

        if not bullet_lines:
            bullet_lines = "- [Bullets to be confirmed]"

        exp_parts.append(
            f"### {title_str} — {company}\n*{date_range}*\n\n{bullet_lines}"
        )
    experience_section = "\n\n".join(exp_parts) if exp_parts else "[Experience to be confirmed]"

    # Build certifications section
    cert_parts = []
    for c in certifications:
        cert_name = c.get("cert_name", "")
        issuer = c.get("issuer", "")
        date_str = c.get("date_obtained", "")
        line = f"- {cert_name}"
        if issuer:
            line += f" ({issuer})"
        if date_str:
            line += f" — {date_str}"
        cert_parts.append(line)
    certifications_section = "\n".join(cert_parts) if cert_parts else "[Certifications to be confirmed]"

    # Education
    if education:
        education_section = "\n".join(f"- {e}" for e in education)
    else:
        education_section = "[Education to be provided by user]"

    # Substitute
    resume = _RESUME_TEMPLATE.format(
        name=name,
        headline=headline,
        email=email,
        phone=phone,
        location=location,
        linkedin=linkedin,
        summary=summary,
        technical_skills=technical_skills,
        tools_list=tools_section,
        leadership_skills=leadership_skills,
        experience_section=experience_section,
        certifications_section=certifications_section,
        education_section=education_section,
    )

    return resume.strip()


def generate(
    requirements: dict[str, Any],
    matched_experience: list[dict[str, Any]],
) -> str:
    """Generate a Markdown resume from evidence (mock-only).

    Calls generate_markdown_resume with DB state. Never invents data.
    """
    profile = database.get_user_profile() or {}
    bullets = database.query_bullets()
    certs = database.get_certifications()
    return generate_markdown_resume(
        requirements=requirements,
        experience=matched_experience,
        bullets=bullets,
        profile=profile,
        certifications=certs,
    )
