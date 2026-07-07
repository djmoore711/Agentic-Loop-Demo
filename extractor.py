"""
Job description extraction from file, raw text, or URL.

Handles three input modes:
  1. File path -> read file contents
  2. Raw text -> use directly
  3. URL -> fetch and parse HTML

For URL mode, tries (in order):
  - JSON-LD JobPosting schema
  - OpenGraph / meta tags
  - Common content containers (<main>, <article>, job-description divs)
  - Fallback to <body> text

If extracted text is very short, warns about possible SPA rendering issues.
"""

from __future__ import annotations

import json
import os

import requests
from bs4 import BeautifulSoup

from models import JobDescription

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
MIN_VALID_TEXT_LENGTH = 100


def extract_from_file(file_path: str) -> JobDescription:
    """Read a job description from a local file."""
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    return JobDescription(
        raw_text=text.strip(),
        source_url="",
        extraction_method="file",
    )


def extract_from_text(text: str) -> JobDescription:
    """Build a JobDescription from raw pasted text."""
    return JobDescription(
        raw_text=text.strip(),
        source_url="",
        extraction_method="text",
    )


def extract_from_url(url: str) -> JobDescription:
    """Fetch and parse a job description from a URL."""
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    title = ""
    company = ""
    location = ""
    extracted_text = ""
    method = "url-body"

    # Try JSON-LD JobPosting
    jsonld = _extract_jsonld(soup)
    if jsonld:
        title = jsonld.get("title", "")
        company = (
            jsonld.get("hiringOrganization", {}).get("name", "")
            if isinstance(jsonld.get("hiringOrganization"), dict)
            else ""
        )
        location = (
            jsonld.get("jobLocation", {}).get("addressLocality", "")
            if isinstance(jsonld.get("jobLocation"), dict)
            else ""
        )
        desc = jsonld.get("description", "")
        if desc:
            # Clean HTML from description if present
            desc_soup = BeautifulSoup(desc, "html.parser")
            extracted_text = desc_soup.get_text(separator="\n", strip=True)
            method = "url-jsonld"
            return JobDescription(
                title=title,
                company=company,
                location=location,
                raw_text=extracted_text,
                source_url=url,
                extraction_method=method,
            )

    # Try OpenGraph / meta tags
    og_title = soup.find("meta", property="og:title")
    if og_title and not title:
        title = og_title.get("content", "")
    meta_desc = soup.find("meta", {"name": "description"})
    if meta_desc and not extracted_text:
        extracted_text = meta_desc.get("content", "")
        method = "url-meta"

    # Try common content containers
    if not extracted_text or len(extracted_text) < MIN_VALID_TEXT_LENGTH:
        for selector in ["main", "article", "[role='main']", ".job-description", "#job-description"]:
            container = soup.select_one(selector)
            if container:
                text = container.get_text(separator="\n", strip=True)
                if len(text) > MIN_VALID_TEXT_LENGTH:
                    extracted_text = text
                    method = "url-meta"
                    break

    # Fallback to body text
    if not extracted_text or len(extracted_text) < MIN_VALID_TEXT_LENGTH:
        extracted_text = soup.get_text(separator="\n", strip=True)
        method = "url-body"

    # Warn if text is suspiciously short
    if len(extracted_text) < MIN_VALID_TEXT_LENGTH:
        extracted_text = (
            extracted_text
            + "\n\n[WARNING: Extracted text is very short. "
            "The page may use JavaScript rendering. "
            "Consider pasting the job description text directly.]"
        )

    return JobDescription(
        title=title,
        company=company,
        location=location,
        raw_text=extracted_text,
        source_url=url,
        extraction_method=method,
    )


def _extract_jsonld(soup: BeautifulSoup) -> dict | None:
    """Try to find and parse a JSON-LD JobPosting script."""
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        # Could be a single object or a list
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict) and item.get("@type") in ("JobPosting", "http://schema.org/JobPosting"):
                return item
            # Some sites nest under @graph
            graph = item.get("@graph", []) if isinstance(item, dict) else []
            if isinstance(graph, list):
                for g in graph:
                    if isinstance(g, dict) and g.get("@type") in ("JobPosting", "http://schema.org/JobPosting"):
                        return g
    return None


def extract(file_path: str | None = None, text: str | None = None, url: str | None = None) -> JobDescription:
    """Dispatch to the correct extraction method based on which argument is provided."""
    if file_path:
        return extract_from_file(file_path)
    elif text:
        return extract_from_text(text)
    elif url:
        return extract_from_url(url)
    else:
        raise ValueError("Must provide one of: file_path, text, or url")
