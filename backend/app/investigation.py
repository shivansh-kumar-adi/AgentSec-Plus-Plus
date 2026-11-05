from __future__ import annotations

import json
from typing import Any


def investigate(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Deterministic, explainable fallback. Untrusted event text is evidence, never instructions."""
    if not events:
        return {"classification": "insufficient_evidence", "severity": 0, "evidence": [],
                "explanation": "No related events are available.", "recommendations": ["Collect more telemetry."],
                "provider": "deterministic-policy"}
    max_severity = max(int(event["severity"]) for event in events)
    types = {event["event_type"] for event in events}
    confirmed = any(json.loads(event["attributes_json"] or "{}").get("confirmed_indicator") is True for event in events)
    if confirmed:
        classification = "confirmed_malicious"
    elif max_severity >= 7 or "detection" in types:
        classification = "suspicious_unconfirmed"
    elif max_severity <= 2:
        classification = "benign"
    else:
        classification = "insufficient_evidence"
    evidence = [{"event_id": event["id"], "type": event["event_type"],
                 "severity": event["severity"], "occurred_at": event["occurred_at"]} for event in events[:25]]
    recommendations = ["Review the linked raw telemetry and asset owner context."]
    if any(event.get("source_ip") for event in events):
        recommendations.append("Validate the source IP before requesting a time-bounded network block.")
    if any(event.get("process_id") is not None for event in events):
        recommendations.append("Verify process identity, parentage, and executable signature before termination.")
    return {"classification": classification, "severity": max_severity, "evidence": evidence,
            "explanation": f"Policy classified {len(events)} related event(s); maximum observed severity is {max_severity}.",
            "recommendations": recommendations, "provider": "deterministic-policy"}

