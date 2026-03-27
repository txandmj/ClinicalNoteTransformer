"""Builds versioned CoT prompts for Claude from config + request context."""

from app.prompts.config import PROMPT_VERSION, load_cot_template
from app.schemas import GenerateRequest


def build_system_prompt() -> str:
    base = load_cot_template(PROMPT_VERSION)
    return f"[prompt_version={PROMPT_VERSION}]\n\n{base}"


def build_user_prompt(req: GenerateRequest) -> str:
    parts = [
        "## Source clinical note(s)\n",
        req.note_text.strip(),
        "\n",
    ]
    if req.guideline_text:
        parts.extend(["## Admission guideline (reference)\n", req.guideline_text.strip(), "\n"])
    if req.reference_pattern_text:
        parts.extend(
            [
                "## Reference transformation pattern (from exemplar case)\n",
                req.reference_pattern_text.strip(),
                "\n",
            ]
        )
    parts.append(
        "Respond with a single JSON object only, keys as specified in the system prompt. "
        "No prose outside JSON."
    )
    return "".join(parts)
