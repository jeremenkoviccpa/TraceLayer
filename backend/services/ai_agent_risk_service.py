"""Risk scoring engine for AI agent events.

Scores based on:
  - Data sensitivity (what categories moved)
  - Action type (read vs write vs delete)
  - Chain depth (direct call vs agent-called-by-agent)
  - Specific risk flags (unauthenticated endpoint, cross-border, PII exfiltration)
"""

SENSITIVE_DATA = {"health", "biometric", "financial", "payment", "credentials"}
PERSONAL_DATA  = {"pii", "personal", "email", "location"}

ACTION_RISK = {
    "data_delete":    3,
    "data_write":     2,
    "api_call":       1,
    "function_call":  1,
    "tool_use":       1,
    "data_read":      0,
}

FLAG_RISK = {
    "pii_exfiltration":         4,
    "unauthenticated_endpoint": 3,
    "cross_border":             2,
    "chain_escalation":         2,
    "unreviewed_tool":          1,
    "high_volume":              1,
}


def compute_risk(
    data_categories: list[str],
    action_type: str,
    chain_depth: int,
    risk_flags: list[str],
) -> str:
    score = 0

    # Data sensitivity
    cats = {c.lower() for c in data_categories}
    if cats & SENSITIVE_DATA:
        score += 3
    elif cats & PERSONAL_DATA:
        score += 2
    elif cats:
        score += 1

    # Action type
    score += ACTION_RISK.get(action_type, 0)

    # Chain depth — agent calling agent is exponentially riskier
    if chain_depth >= 3:
        score += 3
    elif chain_depth >= 2:
        score += 2
    elif chain_depth >= 1:
        score += 1

    # Specific flags
    for flag in risk_flags:
        score += FLAG_RISK.get(flag, 0)

    if score >= 7:
        return "critical"
    elif score >= 4:
        return "high"
    elif score >= 2:
        return "medium"
    return "low"


def infer_risk_flags(
    data_categories: list[str],
    target_url: str | None,
    chain_depth: int,
    action_type: str,
) -> list[str]:
    """Auto-infer risk flags from event properties when not explicitly provided."""
    flags: list[str] = []
    cats = {c.lower() for c in data_categories}

    if cats & SENSITIVE_DATA and action_type in ("api_call", "data_write"):
        flags.append("pii_exfiltration")

    if target_url and target_url.startswith("http://"):
        flags.append("unauthenticated_endpoint")

    if chain_depth >= 2:
        flags.append("chain_escalation")

    return flags
