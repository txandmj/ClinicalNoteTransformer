"""Map structured clinical output to a minimal FHIR R4 Bundle (interoperability demo)."""

from __future__ import annotations

import html
import uuid
from datetime import datetime, timezone
from typing import Any

from app.schemas import StructuredClinicalOutput


def _narrative_div(text: str) -> dict[str, str]:
    esc = html.escape(text or "", quote=True)
    return {
        "status": "generated",
        "div": f'<div xmlns="http://www.w3.org/1999/xhtml"><p>{esc}</p></div>',
    }


def structured_to_fhir_bundle(output: StructuredClinicalOutput) -> dict[str, Any]:
    """Return a FHIR R4 Bundle (type=collection) — not a complete clinical document."""
    patient_id = str(uuid.uuid4())
    encounter_id = str(uuid.uuid4())
    composition_id = str(uuid.uuid4())

    patient_ref = f"Patient/{patient_id}"
    encounter_ref = f"Encounter/{encounter_id}"

    patient: dict[str, Any] = {
        "resourceType": "Patient",
        "id": patient_id,
        "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/Patient"]},
        "identifier": [
            {
                "system": "http://terminology.hl7.org/NamingSystem/v2-0203",
                "value": f"deidentified-{patient_id[:8]}",
            }
        ],
    }

    encounter: dict[str, Any] = {
        "resourceType": "Encounter",
        "id": encounter_id,
        "status": "unknown",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "AMB",
            "display": "ambulatory",
        },
        "subject": {"reference": patient_ref},
    }

    sections: list[dict[str, Any]] = []
    if output.chief_complaint.strip():
        sections.append(
            {
                "title": "Chief complaint",
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "8661-1",
                            "display": "Chief Complaint",
                        }
                    ]
                },
                "text": _narrative_div(output.chief_complaint),
            }
        )
    if output.original_hpi.strip():
        sections.append(
            {
                "title": "History of present illness (original)",
                "text": _narrative_div(output.original_hpi),
            }
        )
    if output.revised_hpi.strip():
        sections.append(
            {
                "title": "History of present illness (revised)",
                "text": _narrative_div(output.revised_hpi),
            }
        )
    if output.hpi_summary.strip():
        sections.append(
            {
                "title": "HPI summary",
                "text": _narrative_div(output.hpi_summary),
            }
        )

    disp_obs_id = str(uuid.uuid4())
    disposition_obs: dict[str, Any] = {
        "resourceType": "Observation",
        "id": disp_obs_id,
        "status": "final",
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "83906-8",
                    "display": "Assessment note",
                }
            ],
            "text": "Disposition recommendation",
        },
        "subject": {"reference": patient_ref},
        "encounter": {"reference": encounter_ref},
        "valueString": output.disposition_recommendation.value,
    }

    sections.append(
        {
            "title": "Disposition",
            "entry": [{"reference": f"Observation/{disp_obs_id}"}],
        }
    )

    composition: dict[str, Any] = {
        "resourceType": "Composition",
        "id": composition_id,
        "status": "preliminary",
        "type": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "51848-0",
                    "display": "Clinical note",
                }
            ]
        },
        "subject": {"reference": patient_ref},
        "encounter": {"reference": encounter_ref},
        "date": datetime.now(timezone.utc).isoformat(),
        "author": [{"display": "Clinical Note Transformer (automated export)"}],
        "title": "Structured clinical summary export",
        "section": sections,
    }

    entry_resources: list[tuple[str, dict[str, Any]]] = [
        (patient_id, patient),
        (encounter_id, encounter),
        (composition_id, composition),
        (disp_obs_id, disposition_obs),
    ]

    for finding in output.key_findings:
        if not finding.strip():
            continue
        oid = str(uuid.uuid4())
        obs = {
            "resourceType": "Observation",
            "id": oid,
            "status": "final",
            "code": {"text": "Key finding"},
            "subject": {"reference": patient_ref},
            "valueString": finding,
        }
        entry_resources.append((oid, obs))

    for cond in output.suspected_conditions:
        if not cond.strip():
            continue
        cid = str(uuid.uuid4())
        condition = {
            "resourceType": "Condition",
            "id": cid,
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active",
                    }
                ]
            },
            "verificationStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                        "code": "unconfirmed",
                    }
                ]
            },
            "subject": {"reference": patient_ref},
            "code": {"text": cond},
        }
        entry_resources.append((cid, condition))

    for unc in output.uncertainties:
        if not unc.strip():
            continue
        nid = str(uuid.uuid4())
        note = {
            "resourceType": "Observation",
            "id": nid,
            "status": "final",
            "code": {"text": "Clinical uncertainty"},
            "subject": {"reference": patient_ref},
            "valueString": unc,
        }
        entry_resources.append((nid, note))

    entries: list[dict[str, Any]] = []
    for rid, resource in entry_resources:
        rt = resource["resourceType"]
        entries.append(
            {
                "fullUrl": f"urn:uuid:{rid}",
                "resource": resource,
                "request": {"method": "POST", "url": rt},
            }
        )

    return {
        "resourceType": "Bundle",
        "id": str(uuid.uuid4()),
        "type": "collection",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entry": entries,
    }
