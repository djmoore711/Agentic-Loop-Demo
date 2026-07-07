# Job Description Extraction Patterns

This document describes how the extractor handles different job posting sources, and their limitations.

## Input Methods

### File
Reads the file contents directly. Most reliable method.

### Raw Text
Uses the text as-is. Second most reliable. Recommended when a URL fails to produce usable content.

### URL
Fetches the page and parses HTML. Reliability depends on the platform.

## URL Parsing Strategy (in order)

1. **JSON-LD JobPosting schema** - Many ATS platforms embed structured JobPosting data. This is the most reliable automated extraction.
2. **OpenGraph / meta tags** - Fallback for title and summary.
3. **Common content containers** - `<main>`, `<article>`, `[role='main']`, `.job-description`, `#job-description`.
4. **Body text** - Last resort. Noisy but usable.

If extracted text is under 100 characters, a warning is appended recommending pasted text.

## Platform Notes

### Greenhouse
- Usually has JSON-LD JobPosting schema.
- Extraction should succeed via JSON-LD path.

### Lever
- Often has JSON-LD or well-structured HTML.
- Usually extractable via content containers.

### Workday
- Heavy JavaScript rendering.
- JSON-LD may be present but body content is often client-rendered.
- Recommendation: paste the job description text directly.

### LinkedIn
- Requires authentication for full job descriptions.
- Most content is behind a login wall.
- Recommendation: paste the job description text directly.

### Indeed / Glassdoor
- May have JSON-LD.
- Often wrapped in tracking and advertising HTML.
- Content container fallback usually works.

### Generic company career pages
- Highly variable.
- JSON-LD if present, otherwise content container or body text.

## Known Limitations

- **JavaScript-rendered SPAs**: Pages that render content via JavaScript will return minimal text. The extractor does not run JavaScript. Use file or raw text input for these.
- **Authentication-walled pages**: LinkedIn and some internal ATS portals require login. The extractor will not authenticate.
- **Aggressive anti-bot protection**: Some sites block non-browser User-Agents. The extractor uses a browser-like User-Agent but may still fail.
- **Rate limiting**: Repeated URL extraction may trigger rate limits.

## Recommendation

For best results, copy the job description text and either:
- save it to a file and use `--file`, or
- paste it using `--text` or interactive mode.
