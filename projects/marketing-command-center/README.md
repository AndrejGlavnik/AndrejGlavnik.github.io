
# Commercial Performance & Promotion Intelligence

Decision-focused BI/Data Analyst portfolio project using deterministic synthetic data.

## Decision

Where should a fictional commercial team reallocate next-quarter promotional investment to protect net revenue and improve gross margin without avoidable volume loss?

## Reproduce

From the repository root:

```bash
python3 scripts/build_analytics_projects.py --project commercial
python3 scripts/validate_portfolio_data.py --project commercial
```

## Evidence

- Raw grain: one row per date × SKU × market × channel
- Rows: 139,776
- Period: 1 Jan 2025–30 Jun 2026
- Seed: 41001
- Executed SQL: `sql/analytics.sql`
- Executed notebook: `notebooks/analysis.ipynb`
- Canonical portable artifact: `artifact.json` → `index.html`

All companies, products, values and outcomes are fictional. Promotion ROI uses a modeled baseline and must not be interpreted as a causal estimate.
