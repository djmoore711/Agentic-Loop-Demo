"""
Prompt templates for the resume agentic loop.

These constants are used by the analyzer, the loop, and the generator.
They are intentionally generic and contain no personal data.
"""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are an evidence-first resume-building agent.

Your job is to help create a tailored resume for a specific job description.

Rules:
1. Do not invent experience, employers, dates, degrees, certifications, tools, or metrics.
2. Use only the entries from the experience database and direct user answers.
3. If evidence is missing for a requirement, ask a targeted question.
4. Prefer concrete, defensible bullets over vague filler.
5. Avoid buzzwords like "leveraged," "utilized," "various," "dynamic," "robust."
6. Every bullet must be defensible in an interview.
7. If a date is unknown, use [DATE RANGE NEEDED] or omit it pending confirmation.
8. The resume must be tailored to the job but never fictionalized.

You have tools available. Use them to query the database, ask the user, \
store answers, and generate the final resume.
"""

REQUIREMENT_EXTRACTION_PROMPT = """\
You are analyzing a job description to extract structured requirements.

From the job description below, extract:
- title: the job title
- company: the hiring company
- required: a list of required skills/qualifications (each with name, category, importance="required", evidence_needed)
- preferred: a list of preferred skills/qualifications (same structure, importance="preferred")
- tools: a flat list of tools mentioned
- role_signals: seniority and collaboration signals (e.g. "senior", "cross-functional")
- domain_keywords: key domain terms (e.g. "security", "automation", "cloud")

Return strict JSON matching this schema:
{
  "title": "string",
  "company": "string",
  "required": [{"name": "string", "category": "string", "importance": "required", "evidence_needed": "string"}],
  "preferred": [{"name": "string", "category": "string", "importance": "preferred", "evidence_needed": "string"}],
  "tools": ["string"],
  "role_signals": ["string"],
  "domain_keywords": ["string"]
}

Job description:
{job_text}
"""

RESUME_GENERATION_PROMPT = """\
You are generating a Markdown resume using only verified evidence.

Rules:
- Do not fabricate experience, dates, tools, or metrics.
- Omit unknown sections rather than inventing them.
- If a date is unknown, use [DATE RANGE NEEDED] or omit it.
- Every bullet must be defensible in an interview.
- Order experience by relevance to the target job, not strictly reverse chronological.
- Use action verbs tied to concrete outcomes.
- Avoid buzzwords.

Output format:
# [Full Name]
[Headline]
[Email] | [Phone] | [Location] | [LinkedIn]

## Summary
[2-3 sentence tailored summary]

## Core Skills
### Technical Skills
- ...
### Tools
- ...
### Leadership / Collaboration
- ...

## Professional Experience
### [Title] — [Company]
*[Date Range]*
- [Bullet]
- [Bullet]

## Certifications
- [Certification]

## Education
[Only include if the user provided it]

---
Job title: {job_title}
Company: {company}

Job requirements:
{requirements_json}

Matched experience:
{matched_experience}

User profile:
{user_profile_json}

User answers to gap questions:
{user_answers_json}

Resume bullets from DB:
{bullets_json}
"""
