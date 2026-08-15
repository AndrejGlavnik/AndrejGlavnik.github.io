
# Data contract

- Pipeline grain: one row per scheduled date × asset.
- Quality grain: one row per pipeline run × quality rule.
- Required dimensions: asset, run date, rule, severity, threshold, owner and evidence path.
- Critical thresholds: no duplicate business keys, at least 90% partition coverage and no more than 0.5% reconciliation variance.
- A missing partition is not treated as a healthy zero.
