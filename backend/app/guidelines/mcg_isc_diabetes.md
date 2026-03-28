# MCG-style placeholder — Diabetes / metabolic (ISC)

Replace this file with your real **MCG ISC** diabetes admission criteria text. Keep the
preset id `MCG_ISC_DIABETES` in `registry.json` so the app can load it by key.

When this file is large and reused across many `/generate` calls, **Anthropic prompt
caching** (ephemeral breakpoints) applies to this block so repeated requests pay
lower input-token cost for the cached portion.

Suggested sections when you paste real content:
- Target population and admission triggers
- Severity / objective thresholds (e.g. DKA, hypoglycemia, HHS) if applicable
- Observation vs inpatient when noted
- Documentation elements expected for level-of-care justification
