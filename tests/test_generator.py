"""Tests for generator.py — template substitution and fallback behavior."""

import pytest
from generator import generate_markdown_resume


class TestGenerateMarkdownResume:
    """generate_markdown_resume builds Markdown from evidence dicts."""

    def test_basic_resume_has_sections(self):
        requirements = {"title": "Security Engineer", "company": "Acme", "domain_keywords": ["security"]}
        experience = [{"company": "Old Corp", "title": "Engineer", "date_range": "2020-2022", "details": "Did stuff"}]
        bullets = [{"company": "Old Corp", "bullet_text": "Automated something", "experience_id": 1}]
        profile = {"full_name": "Alex C.", "headline": "Engineer", "email": "a@b.com", "phone": "555", "location": "Remote", "linkedin": "https://"}
        certifications = []

        resume = generate_markdown_resume(requirements, experience, bullets, profile, certifications)

        assert "# Alex C." in resume
        assert "Engineer" in resume
        assert "Security Engineer" in resume
        assert "Old Corp" in resume
        assert "Automated something" in resume

    def test_fallback_skills_when_no_requirements(self):
        requirements = {}
        experience = []
        bullets = []
        profile = {"full_name": "Test", "headline": "", "email": "", "phone": "", "location": "", "linkedin": ""}
        certifications = []

        resume = generate_markdown_resume(requirements, experience, bullets, profile, certifications)

        assert "[Skills to be confirmed]" in resume
        assert "[Tools to be confirmed]" in resume
        assert "[Experience to be confirmed]" in resume

    def test_certifications_shown(self):
        requirements = {}
        experience = []
        bullets = []
        profile = {"full_name": "Test", "headline": "", "email": "", "phone": "", "location": "", "linkedin": ""}
        certifications = [{"cert_name": "CISSP", "issuer": "ISC2", "date_obtained": "2022"}]

        resume = generate_markdown_resume(requirements, experience, bullets, profile, certifications)

        assert "CISSP" in resume
        assert "ISC2" in resume
        assert "2022" in resume

    def test_fallback_profile_fields(self):
        requirements = {}
        experience = []
        bullets = []
        profile = {}
        certifications = []

        resume = generate_markdown_resume(requirements, experience, bullets, profile, certifications)

        assert "[Name Needed]" in resume
        assert "[Email Needed]" in resume

    def test_no_bullets_uses_details(self):
        """When no matching bullets exist, fall back to experience details."""
        requirements = {"title": "Role", "company": ""}
        experience = [{"company": "Firm", "title": "Analyst", "date_range": "2019-2021", "details": "Did security analysis work"}]
        bullets = []
        profile = {"full_name": "T", "headline": "", "email": "", "phone": "", "location": "", "linkedin": ""}
        certifications = []

        resume = generate_markdown_resume(requirements, experience, bullets, profile, certifications)

        assert "Did security analysis work" in resume
