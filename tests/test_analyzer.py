"""Tests for analyzer.py — keyword matching, title/company extraction."""

import pytest
from analyzer import analyze_mock
from models import JobDescription


class TestAnalyzeMock:
    """analyze_mock extracts requirements from job description text."""

    def test_extracts_skills_from_text(self):
        jd = JobDescription(raw_text="We need a Python developer with AWS and Kubernetes experience")
        result = analyze_mock(jd)
        names = [r["name"] for r in result["required"]]
        assert "Python" in names
        # "aws" is 3 chars → upper(): "AWS"
        assert "AWS" in names
        assert "Kubernetes" in names

    def test_dedup_skills(self):
        """Same keyword appearing multiple times should not produce duplicate entries."""
        jd = JobDescription(raw_text="Python Python Python")
        result = analyze_mock(jd)
        python_count = sum(1 for r in result["required"] if r["name"] == "Python")
        assert python_count == 1

    def test_falls_back_title_from_first_line(self):
        jd = JobDescription(raw_text="Senior Security Engineer\nSome company\nDetails here")
        result = analyze_mock(jd)
        assert "Senior Security Engineer" in result["title"]

    def test_falls_back_company_from_at_pattern(self):
        jd = JobDescription(raw_text="Security Engineer at CyberCorp\nResponsibilities include...")
        result = analyze_mock(jd)
        assert result["company"] == "CyberCorp"

    def test_detects_role_signals(self):
        jd = JobDescription(raw_text="Looking for a senior lead engineer with management experience")
        result = analyze_mock(jd)
        assert "senior" in result["role_signals"]
        assert "lead" in result["role_signals"]
        # "management" text — "manager" is not a substring, so not in signals
        # (the signal list is matched by exact keyword presence, not stemming)

    def test_detects_domain_keywords(self):
        jd = JobDescription(raw_text="Security automation in cloud infrastructure")
        result = analyze_mock(jd)
        assert "security" in result["domain_keywords"]
        assert "automation" in result["domain_keywords"]
        assert "cloud" in result["domain_keywords"]

    def test_handles_empty_text(self):
        jd = JobDescription(raw_text="")
        result = analyze_mock(jd)
        assert result["title"] == ""
        assert result["company"] == ""
        assert result["required"] == []
        assert result["domain_keywords"] == []

    def test_security_tools_get_added_to_tools_list(self):
        jd = JobDescription(raw_text="Experience with Splunk and Wiz")
        result = analyze_mock(jd)
        # "splunk" is 6 chars → title(): "Splunk"
        # "wiz" is 3 chars → upper(): "WIZ"
        assert any("Splunk" in t for t in result["tools"])
        assert any("WIZ" in t for t in result["tools"])
