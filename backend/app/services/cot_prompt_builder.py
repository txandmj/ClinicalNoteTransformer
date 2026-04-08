"""Builds versioned CoT prompts for Claude from config + request context."""

from __future__ import annotations

from typing import Any

from app.prompts.config import PROMPT_VERSION, load_cot_template


def build_system_prompt() -> str:
    base = load_cot_template(PROMPT_VERSION)
    return f"[prompt_version={PROMPT_VERSION}]\n\n{base}"


def build_system_param(system_text: str, use_anthropic_api_prompt_prefix_cache: bool) -> str | list[dict[str, Any]]:
    """Anthropic vendor prompt-prefix cache (cache_control), not app generate_response_cache."""
    if use_anthropic_api_prompt_prefix_cache:
        return [{"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}]
    return system_text


def compose_source_clinical_notes(er_note: str | None, hp_note: str | None, note_text: str) -> str:
    """Labeled ER / H&P / other for the model (patient-specific, not cached)."""
    parts: list[str] = []
    if er_note and er_note.strip():
        parts.append("### Emergency department (ER) note\n" + er_note.strip())
    if hp_note and hp_note.strip():
        parts.append("### History & physical (H&P) note\n" + hp_note.strip())
    if note_text and note_text.strip():
        parts.append("### Additional or combined clinical note(s)\n" + note_text.strip())
    return "\n\n".join(parts)


def build_user_content_blocks(
    er_note: str | None,
    hp_note: str | None,
    note_text: str,
    guideline_merged: str | None,
    reference_pattern_text: str | None,
    exemplar_revised_hpi: str | None,
    use_anthropic_api_prompt_prefix_cache: bool,
) -> list[dict[str, Any]]:
    """
    Order: static (Anthropic cache_control-friendly) → dynamic patient notes.

    Static: guideline, reference rubric, human exemplar revised HPI (Case A teaching).
    Dynamic: labeled ER / H&P / other + JSON instruction.
    """
    blocks: list[dict[str, Any]] = []
    if guideline_merged and guideline_merged.strip():
        b: dict[str, Any] = {
            "type": "text",
            "text": "## Admission guideline (reference)\n" + guideline_merged.strip(),
        }
        if use_anthropic_api_prompt_prefix_cache:
            b["cache_control"] = {"type": "ephemeral"}
        blocks.append(b)
    if reference_pattern_text and reference_pattern_text.strip():
        b = {
            "type": "text",
            "text": "## Reference transformation pattern (from exemplar case)\n"
            + reference_pattern_text.strip(),
        }
        if use_anthropic_api_prompt_prefix_cache:
            b["cache_control"] = {"type": "ephemeral"}
        blocks.append(b)
    if exemplar_revised_hpi and exemplar_revised_hpi.strip():
        b = {
            "type": "text",
            "text": (
                "## Exemplar: human revised HPI (reference case — teaching only)\n\n"
                "Below is a **human-written** revised HPI from a **different (reference)** case. "
                "Use it only to learn structure, tone, and how to link narrative to admission "
                "criteria. Do **not** copy patient-specific facts from the exemplar into your "
                "output. Every clinical fact in your JSON must come from the **current** "
                "ER/H&P (and additional notes) in the next section.\n\n"
                + exemplar_revised_hpi.strip()
            ),
        }
        if use_anthropic_api_prompt_prefix_cache:
            b["cache_control"] = {"type": "ephemeral"}
        blocks.append(b)
    closing = (
        "\n\nRespond with a single JSON object only, keys as specified in the system prompt. "
        "No prose outside JSON."
    )
    body = compose_source_clinical_notes(er_note, hp_note, note_text)
    blocks.append(
        {
            "type": "text",
            "text": "## Current case — source clinical material (ground truth)\n" + body + closing,
        }
    )
    return blocks
