"""Anthropic Claude — clinical chain-of-thought structured extraction."""

import json
import re
from typing import Any

from anthropic import Anthropic

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
    return json.loads(text)


def _parse_structured(data: dict[str, Any]) -> StructuredClinicalOutput:
    disp_raw = data.get("disposition_recommendation") or "Unknown"
    try:
        disp = Disposition(str(disp_raw).strip())
    except ValueError:
        disp = Disposition.UNKNOWN
    return StructuredClinicalOutput(
        chief_complaint=str(data.get("chief_complaint") or ""),
        hpi_summary=str(data.get("hpi_summary") or ""),
        key_findings=list(data.get("key_findings") or []),
        suspected_conditions=list(data.get("suspected_conditions") or []),
        disposition_recommendation=disp,
        uncertainties=list(data.get("uncertainties") or []),
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
    text_blocks = [b.text for b in message.content if b.type == "text"]
    raw = "".join(text_blocks).strip()

    data = _extract_json_object(raw)
    structured = _parse_structured(data)

    return GenerateResponse(
        structured=structured,
        prompt_version=PROMPT_VERSION,
        model=settings.anthropic_model,
        raw_cot_trace=None,
    )
