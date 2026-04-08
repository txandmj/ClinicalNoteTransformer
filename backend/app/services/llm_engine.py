"""Anthropic Claude — clinical chain-of-thought structured extraction."""

import json
import re
from typing import Any

from anthropic import Anthropic
from anthropic.types import TextBlock

from app.core.config import Settings
from app.deidentify import deidentify_note
from app.prompts.config import PROMPT_VERSION
from app.schemas import (
    Disposition,
    GenerateRequest,
    GenerateResponse,
    SentenceComparisonItem,
    StructuredClinicalOutput,
    TokenUsage,
)
from app.services.clinical_abbreviations import expand_structured_revised_hpi_fields
from app.services.cot_prompt_builder import (
    build_system_param,
    build_system_prompt,
    build_user_content_blocks,
)


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    fence = re.match(r"^```(?:json)?\s*([\s\S]*?)```\s*$", text)
    if fence:
        text = fence.group(1).strip()
    try:
        parsed: Any = json.loads(text)
    except json.JSONDecodeError as e:
        snippet = text[:500] + ("…" if len(text) > 500 else "")
        raise ValueError(f"Model output was not valid JSON: {e}; snippet: {snippet!r}") from e
    if not isinstance(parsed, dict):
        raise ValueError("Model JSON must be an object at the top level")
    return parsed


def _coerce_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        return [str(value)]
    return [str(item) for item in value]


def _parse_sentence_comparisons(value: Any) -> list[SentenceComparisonItem]:
    if value is None or not isinstance(value, list):
        return []
    out: list[SentenceComparisonItem] = []
    for i, item in enumerate(value):
        if not isinstance(item, dict):
            continue
        idx = item.get("sentence_index")
        try:
            sentence_index_stored = int(idx) if idx is not None else i + 1
        except (TypeError, ValueError):
            sentence_index_stored = i + 1
        out.append(
            SentenceComparisonItem(
                sentence_index=sentence_index_stored,
                revised=str(item.get("revised") or ""),
                source=str(item.get("source") or ""),
                reason=str(item.get("reason") or ""),
            )
        )
    return out


def _parse_structured(data: dict[str, Any]) -> StructuredClinicalOutput:
    disp_raw = data.get("disposition_recommendation") or "Unknown"
    try:
        disp = Disposition(str(disp_raw).strip())
    except ValueError:
        disp = Disposition.UNKNOWN
    return StructuredClinicalOutput(
        chief_complaint=str(data.get("chief_complaint") or ""),
        original_hpi=str(data.get("original_hpi") or ""),
        hpi_summary=str(data.get("hpi_summary") or ""),
        key_findings=_coerce_str_list(data.get("key_findings")),
        suspected_conditions=_coerce_str_list(data.get("suspected_conditions")),
        disposition_recommendation=disp,
        uncertainties=_coerce_str_list(data.get("uncertainties")),
        revised_hpi=str(data.get("revised_hpi") or ""),
        sentence_comparisons=_parse_sentence_comparisons(data.get("sentence_comparisons")),
    )


def generate_structured(
    req: GenerateRequest,
    settings: Settings,
    guideline_merged: str | None,
) -> GenerateResponse:
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured")

    client = Anthropic(api_key=settings.anthropic_api_key)
    use_cache = settings.anthropic_prompt_cache
    system_text = build_system_prompt()
    system_param = build_system_param(system_text, use_cache)

    # De-identify source note content before assembling model prompt blocks.
    er_note = deidentify_note(req.er_note)
    hp_note = deidentify_note(req.hp_note)
    other_note = deidentify_note(req.note_text) or ""

    user_blocks = build_user_content_blocks(
        er_note,
        hp_note,
        other_note,
        guideline_merged,
        req.reference_pattern_text,
        req.exemplar_revised_hpi,
        use_cache,
    )

    message = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=8192,
        system=system_param,
        messages=[{"role": "user", "content": user_blocks}],
    )
    text_blocks: list[str] = []
    for block in message.content:
        if isinstance(block, TextBlock):
            text_blocks.append(block.text)
    raw = "".join(text_blocks).strip()

    data = _extract_json_object(raw)
    structured = expand_structured_revised_hpi_fields(_parse_structured(data))

    usage: TokenUsage | None = None
    u = message.usage
    if u is not None:
        usage = TokenUsage(
            input_tokens=u.input_tokens,
            output_tokens=u.output_tokens,
            cache_read_input_tokens=u.cache_read_input_tokens,
            cache_creation_input_tokens=u.cache_creation_input_tokens,
        )

    return GenerateResponse(
        structured=structured,
        prompt_version=PROMPT_VERSION,
        model=settings.anthropic_model,
        raw_cot_trace=None,
        usage=usage,
    )
