"""Anthropic Claude — clinical chain-of-thought structured extraction."""

import json
import re
from typing import Any

from anthropic import Anthropic
from anthropic.types import TextBlock

from app.generate_response_cache import (
    generate_response_cache_fingerprint,
    get_lru_generate_response_cache,
)
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

# Rough input token budget when tiktoken is not used (~4 chars/token for English prose).
_CHARS_PER_TOKEN_ESTIMATE = 4
_TRUNC_MARKER = "\n…[truncated for length]"


def _truncate_note_field(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    keep = max_chars - len(_TRUNC_MARKER)
    if keep <= 0:
        return text[:max_chars]
    return text[:keep] + _TRUNC_MARKER


def _optional_note(s: str) -> str | None:
    return s if s.strip() else None


def _lru_generate_response_cache_payload(
    *,
    er_note: str | None,
    hp_note: str | None,
    other_note: str,
    guideline_merged: str | None,
    reference_pattern_text: str | None,
    exemplar_revised_hpi: str | None,
    model: str,
    anthropic_api_prompt_prefix_cache: bool,
) -> dict[str, Any]:
    return {
        "er": er_note or "",
        "hp": hp_note or "",
        "other": other_note,
        "guideline": (guideline_merged or "").strip(),
        "reference": (reference_pattern_text or "").strip(),
        "exemplar": (exemplar_revised_hpi or "").strip(),
        "model": model,
        "prompt_version": PROMPT_VERSION,
        "anthropic_api_prompt_prefix_cache": anthropic_api_prompt_prefix_cache,
    }


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

    use_anthropic_prefix = settings.anthropic_api_prompt_prefix_cache
    system_text = build_system_prompt()
    system_param = build_system_param(system_text, use_anthropic_prefix)

    # De-identify source note content before assembling model prompt blocks.
    er_raw = deidentify_note(req.er_note) or ""
    hp_raw = deidentify_note(req.hp_note) or ""
    other_raw = deidentify_note(req.note_text) or ""

    # Layer 1 — cap each section (~N tokens via char heuristic).
    max_chars = max(
        256,
        settings.generate_max_input_tokens_per_section * _CHARS_PER_TOKEN_ESTIMATE,
    )
    er_note = _optional_note(_truncate_note_field(er_raw, max_chars))
    hp_note = _optional_note(_truncate_note_field(hp_raw, max_chars))
    other_note = _truncate_note_field(other_raw, max_chars)

    # Layer 2 — LRU full JSON response cache (no Anthropic API call on hit).
    if settings.generate_response_cache_enabled and settings.generate_response_cache_max_entries > 0:
        cache_payload = _lru_generate_response_cache_payload(
            er_note=er_note,
            hp_note=hp_note,
            other_note=other_note,
            guideline_merged=guideline_merged,
            reference_pattern_text=req.reference_pattern_text,
            exemplar_revised_hpi=req.exemplar_revised_hpi,
            model=settings.anthropic_model,
            anthropic_api_prompt_prefix_cache=use_anthropic_prefix,
        )
        cache_key = generate_response_cache_fingerprint(cache_payload)
        cache = get_lru_generate_response_cache(settings.generate_response_cache_max_entries)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached.model_copy(update={"from_cache": True, "usage": None})

    client = Anthropic(api_key=settings.anthropic_api_key)

    user_blocks = build_user_content_blocks(
        er_note,
        hp_note,
        other_note,
        guideline_merged,
        req.reference_pattern_text,
        req.exemplar_revised_hpi,
        use_anthropic_prefix,
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

    response = GenerateResponse(
        structured=structured,
        prompt_version=PROMPT_VERSION,
        model=settings.anthropic_model,
        raw_cot_trace=None,
        usage=usage,
        from_cache=False,
    )

    if settings.generate_response_cache_enabled and settings.generate_response_cache_max_entries > 0:
        cache_payload = _lru_generate_response_cache_payload(
            er_note=er_note,
            hp_note=hp_note,
            other_note=other_note,
            guideline_merged=guideline_merged,
            reference_pattern_text=req.reference_pattern_text,
            exemplar_revised_hpi=req.exemplar_revised_hpi,
            model=settings.anthropic_model,
            anthropic_api_prompt_prefix_cache=use_anthropic_prefix,
        )
        cache_key = generate_response_cache_fingerprint(cache_payload)
        get_lru_generate_response_cache(settings.generate_response_cache_max_entries).set(cache_key, response)

    return response
