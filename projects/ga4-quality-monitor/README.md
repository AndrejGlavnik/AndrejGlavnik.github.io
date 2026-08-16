
# Analytics Reliability & Release Control

Analytics delivery and data-quality portfolio project using deterministic synthetic data.

## Decision

Should the next analytics release ship, be held, or ship with an explicitly accepted caveat?

## Reproduce

```bash
python3 scripts/build_analytics_projects.py --project reliability
python3 scripts/validate_portfolio_data.py --project reliability
```

- Source records: 48,770
- Quality results: 2,928
- Period: 1 Mar–30 Jun 2026
- Seed: 42002
- SQL: `sql/analytics.sql`
- Executed notebook: `notebooks/analysis.ipynb`
- Scenario disclosure: `data/scenario-manifest.json`

No employer policy, data or release is represented.
