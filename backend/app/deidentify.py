"""Clinical note de-identification: Presidio (optional) + regex + name fallbacks."""

from __future__ import annotations

import re
import threading
from typing import Any

# Ordered: more specific patterns first (applied after Presidio when available).
PHI_PATTERNS = [
    ("MRN", r"\bMRN[:\s#]*\d+\b"),
    ("SSN", r"\b\d{3}-\d{2}-\d{4}\b"),
    ("PHONE", r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b"),
    ("EMAIL", r"\S+@\S+\.\S+"),
    ("DATE", r"\b(?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12]\d|3[01])[/-]\d{2,4}\b"),
    ("AGE", r"\b(1[2-9]\d|[2-9]\d)\s*(?:year[s]?[-\s]old|y/?o)\b"),
    ("NAME", r"\b(?:Dr\.?|Mr\.?|Mrs\.?|Ms\.?|Prof\.?)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b"),
    ("ZIP", r"\b\d{5}(?:-\d{4})?\b"),
]

# Deny-list noisy entity types / recognizers in clinical context.
_DENY_ENTITIES = {
    "US_DRIVER_LICENSE",
    "US_PASSPORT",
    "ORGANIZATION",
}
_DENY_RECOGNIZER_NAMES = {
    "UsLicenseRecognizer",
    "UsPassportRecognizer",
}

# Clinical tokens that should never be redacted by Presidio (shield then restore).
_CLINICAL_SAFE = [
    "O2",
    "SpO2",
    "FiO2",
    "B12",
    "D3",
    "K2",
    "T3",
    "T4",
    "TSH",
    "pH",
    "pCO2",
    "pO2",
    "HbA1c",
    "A1c",
    "INR",
    "PT",
    "PTT",
    "BMP",
    "CMP",
    "CBC",
    "BP",
    "HR",
    "RR",
    "Temp",
    "IV",
    "IM",
    "PO",
    "SQ",
    "PRN",
    "QD",
    "BID",
    "TID",
    "ER",
    "ICU",
    "ED",
    "OR",
    "CPR",
    "DNR",
    "AED",
]
_SAFE_MAP = {term: f"qxzplhterm{i}qxzplh" for i, term in enumerate(_CLINICAL_SAFE)}
_RESTORE_MAP = {v: k for k, v in _SAFE_MAP.items()}

# Labeled fields: group 1 = label, group 2 = name (fixes broken split on full match).
_LABELED_NAME_RE = re.compile(
    r"""
    (?ix)
    \b
    (
        patient | pt | name | client |
        referred\s+by | seen\s+by |
        attending | resident | provider |
        parent | guardian | next\s+of\s+kin |
        authorized\s+by | signed\s+by |
        dictated\s+by | transcribed\s+by
    )
    \s*[:#\-]\s*
    (
        [A-Z][a-z]{1,24}(?:\s+[A-Z][a-z]{0,24}){1,2}
    )
    \b
    """,
    re.VERBOSE,
)

_TITLED_NAME_RE = re.compile(
    r"\b(Dr\.?|Mr\.?|Mrs\.?|Ms\.?|Prof\.?)\s+([A-Z][a-z]{1,24})(\s+[A-Z][a-z]{1,24})?\b"
)

_POSSESSIVE_NAME_RE = re.compile(r"\b([A-Z][a-z]{1,24}\s+[A-Z][a-z]{1,24})'s\b")

_NARRATIVE_NAME_RE = re.compile(
    r"""
    (?ix)
    \b(?:patient|pt)\s+
    ([A-Z][a-z]{1,24}\s+[A-Z][a-z]{1,24})
    \b
    """,
    re.VERBOSE,
)

_lock = threading.Lock()
_presidio_analyzer: Any = None
_presidio_anonymizer: Any = None
_presidio_init_failed: bool = False


def _protect_clinical_terms(text: str) -> str:
    for term, placeholder in _SAFE_MAP.items():
        # Case-sensitive: avoids matching common words like "or" / "er".
        text = re.sub(rf"\b{re.escape(term)}\b", placeholder, text)
    return text


def _restore_clinical_terms(text: str) -> str:
    for placeholder, term in _RESTORE_MAP.items():
        text = text.replace(placeholder, term)
    return text


def _init_presidio() -> tuple[Any | None, Any | None]:
    global _presidio_analyzer, _presidio_anonymizer, _presidio_init_failed
    with _lock:
        if _presidio_init_failed:
            return None, None
        if _presidio_analyzer is not None and _presidio_anonymizer is not None:
            return _presidio_analyzer, _presidio_anonymizer
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_analyzer.nlp_engine import NlpEngineProvider
            from presidio_anonymizer import AnonymizerEngine

            provider = NlpEngineProvider(
                nlp_configuration={
                    "nlp_engine_name": "spacy",
                    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
                }
            )
            nlp_engine = provider.create_engine()
            _presidio_analyzer = AnalyzerEngine(nlp_engine=nlp_engine)

            registry = _presidio_analyzer.registry
            registry.recognizers = [
                r
                for r in registry.recognizers
                if r.name not in _DENY_RECOGNIZER_NAMES
                and not (set(getattr(r, "supported_entities", []) or []) & _DENY_ENTITIES)
                and getattr(r, "supported_entity", None) not in _DENY_ENTITIES
            ]

            _presidio_anonymizer = AnonymizerEngine()
            return _presidio_analyzer, _presidio_anonymizer
        except Exception:
            _presidio_init_failed = True
            _presidio_analyzer = None
            _presidio_anonymizer = None
            return None, None


def presidio_engine_active() -> bool:
    analyzer, anonymizer = _init_presidio()
    return analyzer is not None and anonymizer is not None


def _mask_name_fallbacks(text: str) -> str:
    def _replace_labeled(m: re.Match[str]) -> str:
        label = m.group(1).strip()
        return f"{label}: [NAME]"

    text = _LABELED_NAME_RE.sub(_replace_labeled, text)
    text = _TITLED_NAME_RE.sub("[NAME]", text)
    text = _POSSESSIVE_NAME_RE.sub("[NAME]'s", text)
    def _replace_narrative(m: re.Match[str]) -> str:
        prefix = m.group(0).split()[0]
        return f"{prefix} [NAME]"

    text = _NARRATIVE_NAME_RE.sub(_replace_narrative, text)

    return text


def _deidentify_presidio_layer(text: str) -> str:
    analyzer, anonymizer = _init_presidio()
    if not text.strip() or analyzer is None or anonymizer is None:
        return text
    try:
        protected = _protect_clinical_terms(text)
        results = analyzer.analyze(text=protected, language="en")
        redacted = anonymizer.anonymize(text=protected, analyzer_results=results).text
        return _restore_clinical_terms(redacted)
    except Exception:
        return text


def _apply_regex_layer(text: str) -> str:
    for label, pattern in PHI_PATTERNS:
        text = re.sub(pattern, f"[{label}]", text, flags=re.IGNORECASE)
    return _mask_name_fallbacks(text)


def deidentify_note(text: str | None) -> str | None:
    """Presidio when available, then regex + name patterns."""
    if not text:
        return text
    out = _deidentify_presidio_layer(text)
    return _apply_regex_layer(out)
