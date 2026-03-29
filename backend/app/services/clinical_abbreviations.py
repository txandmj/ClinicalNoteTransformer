"""Expand common clinical abbreviations in prose (clean revised HPI alignment)."""

import re

from app.schemas import SentenceComparisonItem, StructuredClinicalOutput

# (regex pattern, replacement) — order matters; list more specific / longer patterns first.
# Use word boundaries; avoid ambiguous English words (e.g. do not replace case-insensitive "OR").
_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bH\s*&\s*P\b", re.IGNORECASE), "history and physical"),
    (re.compile(r"\bE\.M\.S\.\b", re.IGNORECASE), "Emergency medical services"),
    (re.compile(r"\bEMS\b", re.IGNORECASE), "Emergency medical services"),
    (re.compile(r"\bE\.M\.T\.\b", re.IGNORECASE), "Emergency medical technician"),
    (re.compile(r"\bEMT\b", re.IGNORECASE), "Emergency medical technician"),
    (re.compile(r"\bE\.K\.G\.\b", re.IGNORECASE), "electrocardiogram"),
    (re.compile(r"\bEKG\b"), "electrocardiogram"),
    (re.compile(r"\bE\.C\.G\.\b", re.IGNORECASE), "electrocardiogram"),
    (re.compile(r"\bECG\b"), "electrocardiogram"),
    (re.compile(r"\bICU\b", re.IGNORECASE), "intensive care unit"),
    (re.compile(r"\bMICU\b", re.IGNORECASE), "medical intensive care unit"),
    (re.compile(r"\bSICU\b", re.IGNORECASE), "surgical intensive care unit"),
    (re.compile(r"\bNICU\b", re.IGNORECASE), "neonatal intensive care unit"),
    (re.compile(r"\bPICU\b", re.IGNORECASE), "pediatric intensive care unit"),
    (re.compile(r"\bCCU\b", re.IGNORECASE), "coronary care unit"),
    (re.compile(r"\bSTEMI\b", re.IGNORECASE), "ST-elevation myocardial infarction"),
    (re.compile(r"\bNSTEMI\b", re.IGNORECASE), "non-ST-elevation myocardial infarction"),
    (re.compile(r"\bCOPD\b", re.IGNORECASE), "chronic obstructive pulmonary disease"),
    (re.compile(r"\bCHF\b", re.IGNORECASE), "congestive heart failure"),
    (re.compile(r"\bDKA\b", re.IGNORECASE), "diabetic ketoacidosis"),
    (re.compile(r"\bHHS\b", re.IGNORECASE), "hyperglycemic hyperosmolar state"),
    (re.compile(r"\bCABG\b", re.IGNORECASE), "coronary artery bypass graft"),
    (re.compile(r"\bAFib\b"), "atrial fibrillation"),
    (re.compile(r"\bAF\b"), "atrial fibrillation"),
    (re.compile(r"\bA\.Fib\b", re.IGNORECASE), "atrial fibrillation"),
    (re.compile(r"\bURI\b", re.IGNORECASE), "upper respiratory infection"),
    (re.compile(r"\bUTI\b", re.IGNORECASE), "urinary tract infection"),
    (re.compile(r"\bCVA\b", re.IGNORECASE), "cerebrovascular accident"),
    (re.compile(r"\bTIA\b", re.IGNORECASE), "transient ischemic attack"),
    (re.compile(r"\bNKDA\b", re.IGNORECASE), "no known drug allergies"),
    (re.compile(r"\bNKA\b", re.IGNORECASE), "no known allergies"),
    (re.compile(r"\bNPO\b", re.IGNORECASE), "nothing by mouth"),
    (re.compile(r"\bSTAT\b", re.IGNORECASE), "immediately"),
    (re.compile(r"\bPMH\b", re.IGNORECASE), "past medical history"),
    (re.compile(r"\bPSH\b", re.IGNORECASE), "past surgical history"),
    (re.compile(r"\bBMP\b", re.IGNORECASE), "basic metabolic panel"),
    (re.compile(r"\bCBC\b", re.IGNORECASE), "complete blood count"),
    (re.compile(r"\bCMP\b", re.IGNORECASE), "comprehensive metabolic panel"),
    (re.compile(r"\bLFTs\b", re.IGNORECASE), "liver function tests"),
    (re.compile(r"\bLFT\b", re.IGNORECASE), "liver function test"),
    (re.compile(r"\bINR\b", re.IGNORECASE), "international normalized ratio"),
    (re.compile(r"\bPTT\b", re.IGNORECASE), "partial thromboplastin time"),
    (re.compile(r"\bPT\b"), "prothrombin time"),  # case-sensitive: not "Pt" for patient
    (re.compile(r"\bABG\b", re.IGNORECASE), "arterial blood gas"),
    (re.compile(r"\bVBG\b", re.IGNORECASE), "venous blood gas"),
    (re.compile(r"\bSpO2\b", re.IGNORECASE), "pulse oximetry oxygen saturation"),
    (re.compile(r"\bSpO₂\b"), "pulse oximetry oxygen saturation"),
    (re.compile(r"\bO2\b"), "oxygen"),
    (re.compile(r"\bCPAP\b", re.IGNORECASE), "continuous positive airway pressure"),
    (re.compile(r"\bBiPAP\b", re.IGNORECASE), "bilevel positive airway pressure"),
    (re.compile(r"\bSNF\b", re.IGNORECASE), "skilled nursing facility"),
    (re.compile(r"\bOSH\b", re.IGNORECASE), "outside hospital"),
    (re.compile(r"\bPMD\b", re.IGNORECASE), "primary medical doctor"),
    (re.compile(r"\bPCP\b", re.IGNORECASE), "primary care physician"),
    # Location / facility — uppercase tokens only where common in charts
    (re.compile(r"\bED\b"), "emergency department"),
    (re.compile(r"\bER\b"), "emergency department"),
    (re.compile(r"\bOR\b"), "operating room"),
    (re.compile(r"\bGI\b"), "gastrointestinal"),
    (re.compile(r"\bGU\b"), "genitourinary"),
    (re.compile(r"\bIV\b"), "intravenous"),
    (re.compile(r"\bIM\b"), "intramuscular"),
    (re.compile(r"\bSQ\b"), "subcutaneous"),
    (re.compile(r"\bSubq\b", re.IGNORECASE), "subcutaneous"),
    (re.compile(r"\bNG\b"), "nasogastric"),
    (re.compile(r"\bPRN\b", re.IGNORECASE), "as needed"),
    (re.compile(r"\bBID\b", re.IGNORECASE), "twice daily"),
    (re.compile(r"\bB\.I\.D\.\b", re.IGNORECASE), "twice daily"),
    (re.compile(r"\bTID\b", re.IGNORECASE), "three times daily"),
    (re.compile(r"\bQID\b", re.IGNORECASE), "four times daily"),
    (re.compile(r"\bQD\b", re.IGNORECASE), "once daily"),
    (re.compile(r"\bQHS\b", re.IGNORECASE), "every night at bedtime"),
    (re.compile(r"\bACHS\b", re.IGNORECASE), "before meals and at bedtime"),
    (re.compile(r"\bCT\b"), "computed tomography"),
    (re.compile(r"\bMRI\b", re.IGNORECASE), "magnetic resonance imaging"),
    (re.compile(r"\bCXR\b", re.IGNORECASE), "chest X-ray"),
    (re.compile(r"\bECHO\b", re.IGNORECASE), "echocardiogram"),
    (re.compile(r"\bLOC\b", re.IGNORECASE), "level of consciousness"),
    (re.compile(r"\bGCS\b", re.IGNORECASE), "Glasgow Coma Scale"),
    (re.compile(r"\bHR\b"), "heart rate"),
    (re.compile(r"\bBP\b"), "blood pressure"),
    (re.compile(r"\bRR\b"), "respiratory rate"),
    (re.compile(r"\bWBC\b", re.IGNORECASE), "white blood cell count"),
    (re.compile(r"\bHgb\b", re.IGNORECASE), "hemoglobin"),
    (re.compile(r"\bHct\b", re.IGNORECASE), "hematocrit"),
    (re.compile(r"\bPlt\b", re.IGNORECASE), "platelet count"),
    (re.compile(r"\bPlts\b", re.IGNORECASE), "platelet count"),
    (re.compile(r"\bBUN\b", re.IGNORECASE), "blood urea nitrogen"),
    (re.compile(r"\bCr\b", re.IGNORECASE), "creatinine"),
    (re.compile(r"\bNa\b", re.IGNORECASE), "sodium"),
    (re.compile(r"\bCl\b", re.IGNORECASE), "chloride"),
    (re.compile(r"\bCO2\b"), "carbon dioxide"),
    (re.compile(r"\bGluc\b", re.IGNORECASE), "glucose"),
    (re.compile(r"\bDOB\b", re.IGNORECASE), "date of birth"),
    (re.compile(r"\bDNR\b", re.IGNORECASE), "do not resuscitate"),
    (re.compile(r"\bDNI\b", re.IGNORECASE), "do not intubate"),
]


def expand_clinical_abbreviations(text: str) -> str:
    """Replace known abbreviation tokens with spelled-out forms in narrative prose."""
    if not text or not text.strip():
        return text
    result = text
    for pattern, repl in _PATTERNS:
        result = pattern.sub(repl, result)
    return result


def expand_structured_revised_hpi_fields(out: StructuredClinicalOutput) -> StructuredClinicalOutput:
    """Apply abbreviation expansion to §3 revised HPI and matching §4 `revised` strings."""
    new_rev = expand_clinical_abbreviations(out.revised_hpi)
    new_rows = [
        SentenceComparisonItem(
            sentence_index=r.sentence_index,
            revised=expand_clinical_abbreviations(r.revised),
            source=r.source,
            reason=r.reason,
        )
        for r in out.sentence_comparisons
    ]
    return out.model_copy(update={"revised_hpi": new_rev, "sentence_comparisons": new_rows})
