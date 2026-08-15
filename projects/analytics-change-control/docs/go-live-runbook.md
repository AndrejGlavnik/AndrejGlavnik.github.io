
# Go-live and hypercare runbook

## Before go-live

- Confirm OAuth/API credentials and expiry ownership.
- Lock mapping and schema version.
- Reconcile a representative historical load.
- Complete required UAT and rollback decision.

## Hypercare

- Monitor 401/403 authentication failures.
- Apply bounded exponential backoff to 429 responses.
- Quarantine schema-drift records rather than silently dropping them.
- Reconcile received, accepted and rejected record counts.
- Confirm timezone and deduplication behavior at the daily boundary.
