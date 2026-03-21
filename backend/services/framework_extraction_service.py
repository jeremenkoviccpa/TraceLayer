from __future__ import annotations

"""
Framework extraction service — uses Claude to parse regulation documents
and produce a structured diff of control changes.
"""
import json
import logging
import os
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """You are a compliance framework analyst. You will be given the text of a regulatory document or framework update, and you must extract structured control information from it.

Analyze the document and return a JSON object with this exact structure:

{
  "framework_key": "soc2",
  "detected_version": "2023",
  "summary": "One paragraph summary of what changed",
  "added_controls": [
    {
      "external_id": "CC1.1",
      "name": "Control name",
      "category": "category_slug",
      "description": "Full description of the control requirement"
    }
  ],
  "removed_controls": [
    {
      "external_id": "CC1.1",
      "reason": "Why this was removed or merged"
    }
  ],
  "changed_controls": [
    {
      "external_id": "CC1.1",
      "name": "Updated name if changed",
      "description": "Updated description",
      "change_notes": "What specifically changed"
    }
  ],
  "unchanged_controls": [
    {
      "external_id": "CC1.1"
    }
  ]
}

Rules:
- external_id must exactly match the official control numbering in the document (e.g. CC6.1, A.5.1, 164.308(a)(1))
- category must be a lowercase_underscore slug
- Be precise about what changed vs what is new vs what was removed
- If you cannot determine the version, use null for detected_version
- Return ONLY the JSON object, no other text

Framework being analyzed: {framework_key}
Current version on file: {current_version}

Document content:
{content}"""


async def extract_controls_from_content(
    content: str,
    framework_key: str,
    current_version: str,
) -> dict:
    """
    Send document content to Claude and get back a structured control diff.
    Returns the parsed JSON dict, or raises on failure.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    prompt = EXTRACTION_PROMPT.format(
        framework_key=framework_key,
        current_version=current_version,
        content=content[:40000],  # Truncate to avoid context limits
    )

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-opus-4-6",
                "max_tokens": 8192,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
            },
        )
        response.raise_for_status()
        data = response.json()

    raw_text = data["content"][0]["text"]

    # Parse JSON from response
    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code block
        import re
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
        if match:
            result = json.loads(match.group(1))
        else:
            raise ValueError(f"Could not parse JSON from Claude response: {raw_text[:500]}")

    return result


async def fetch_document_content(url: str) -> str:
    """Fetch the text content of a URL (HTML or plain text)."""
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        response = await client.get(url, headers={"User-Agent": "TraceLayer-Compliance-Monitor/1.0"})
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "html" in content_type:
            # Strip HTML tags for cleaner text
            import re
            text = re.sub(r"<[^>]+>", " ", response.text)
            text = re.sub(r"\s+", " ", text).strip()
            return text
        return response.text


def format_extraction_result_for_review(result: dict) -> str:
    """Format an extraction result as a human-readable summary for admin review."""
    lines = [
        f"Framework: {result.get('framework_key', 'unknown')}",
        f"Detected version: {result.get('detected_version', 'unknown')}",
        f"Summary: {result.get('summary', 'No summary')}",
        "",
        f"Added controls ({len(result.get('added_controls', []))}):",
    ]
    for c in result.get("added_controls", []):
        lines.append(f"  + {c['external_id']}: {c['name']}")
    lines.append(f"\nRemoved controls ({len(result.get('removed_controls', []))}):")
    for c in result.get("removed_controls", []):
        lines.append(f"  - {c['external_id']}: {c.get('reason', '')}")
    lines.append(f"\nChanged controls ({len(result.get('changed_controls', []))}):")
    for c in result.get("changed_controls", []):
        lines.append(f"  ~ {c['external_id']}: {c.get('change_notes', '')}")
    return "\n".join(lines)
