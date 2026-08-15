
# Synthetic incident postmortem: duplicate purchase tracking

The scenario injects duplicate business keys after `REL-001`. The uniqueness and reconciliation controls fail, the release gate resolves to HOLD, raw evidence is retained, and `REL-002` represents the remediation. This is a deterministic demonstration, not a real production incident.
