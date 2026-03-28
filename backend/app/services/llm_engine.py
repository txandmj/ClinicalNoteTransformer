"""Anthropic Claude — clinical chain-of-thought structured extraction."""

import json
import re
from typing import Any

from anthropic import Anthropic
from anthropic.types import TextBlock

from app.core.config import Settings
from app.prompts.config import PROMPT_VERSION
from app.schemas import Disposition, GenerateRequest, GenerateResponse, StructuredClinicalOutput
from app.services.cot_prompt_builder import build_system_prompt, build_user_prompt


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    # Strip optional markdown code fence
    fence = re.match(r"^```(?:json)?\s*([\s\S]*?)```\s*$", text)
    if fence:
        text = fence.group(1).strip()
    try:
        parsed: Any = json.loads(text)
    except json.JSONDecodeError as e:
        snippet = text[:500] + ("…" if len(text) >500 else "")
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


def _parse_structured(data: dict[str, Any]) -> StructuredClinicalOutput:
    disp_raw = data.get("disposition_recommendation") or "Unknown"
    try:
        disp = Disposition(str(disp_raw).strip())
    except ValueError:
        disp = Disposition.UNKNOWN
    return StructuredClinicalOutput(
        chief_complaint=str(data.get("chief_complaint") or ""),
        hpi_summary=str(data.get("hpi_summary") or ""),
        key_findings=_coerce_str_list(data.get("key_findings")),
        suspected_conditions=_coerce_str_list(data.get("suspected_conditions")),
        disposition_recommendation=disp,
        uncertainties=_coerce_str_list(data.get("uncertainties")),
        revised_hpi=str(data.get("revised_hpi") or ""),
    )


def generate_structured(req: GenerateRequest, settings: Settings) -> GenerateResponse:
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured")

    client = Anthropic(api_key=settings.anthropic_api_key)
    system = build_system_prompt()
    user = build_user_prompt(req)

    message = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text_blocks: list[str] = []
    for block in message.content:
        if isinstance(block, TextBlock):
            text_blocks.append(block.text)
    raw = "".join(text_blocks).strip()

    data = _extract_json_object(raw)
    structured = _parse_structured(data)

    return GenerateResponse(
        structured=structured,
        prompt_version=PROMPT_VERSION,
        model=settings.anthropic_model,
        raw_cot_trace=None,
    )
