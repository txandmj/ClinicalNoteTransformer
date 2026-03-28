"""Builds versioned CoT prompts for Claude from config + request context."""

from __future__ import annotations

from typing import Any

from app.prompts.config import PROMPT_VERSION, load_cot_template


def build_system_prompt() -> str:
    base = load_cot_template(PROMPT_VERSION)
    return f"[prompt_version={PROMPT_VERSION}]\n\n{base}"


def build_system_param(system_text: str, use_prompt_cache: bool) -> str | list[dict[str, Any]]:
    if use_prompt_cache:
        return [{"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}]
    return system_text


def build_user_content_blocks(
    note_text: str,
    guideline_merged: str | None,
    reference_pattern_text: str | None,
    use_prompt_cache: bool,
) -> list[dict[str, Any]]:
    """
    Order: static guideline → static reference → dynamic note (for Anthropic prompt caching).
    """
    blocks: list[dict[str, Any]] = []
    if guideline_merged and guideline_merged.strip():
        b: dict[str, Any] = {
            "type": "text",
            "text": "## Admission guideline (reference)\n" + guideline_merged.strip(),
        }
        if use_prompt_cache:
            b["cache_control"] = {"type": "ephemeral"}
        blocks.append(b)
    if reference_pattern_text and reference_pattern_text.strip():
        b = {
            "type": "text",
            "text": "## Reference transformation pattern (from exemplar case)\n"
            + reference_pattern_text.strip(),
        }
        if use_prompt_cache:
            b["cache_control"] = {"type": "ephemeral"}
        blocks.append(b)
    closing = (
        "\n\nRespond with a single JSON object only, keys as specified in the system prompt. "
        "No prose outside JSON."
    )
    blocks.append(
        {
            "type": "text",
            "text": "## Source clinical note(s)\n" + note_text.strip() + closing,
        }
    )
    return blocks
