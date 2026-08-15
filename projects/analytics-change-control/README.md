
# SaaS Implementation & Integration Health

Technical implementation and data-integration portfolio project using deterministic synthetic data.

## Decision

Which implementations risk missing committed go-live, why, and what should happen next?

## Reproduce

```bash
python3 scripts/build_analytics_projects.py --project integration
python3 scripts/validate_portfolio_data.py --project integration
```

- Fictional accounts: 60
- Integration runs: 9,192
- Seed: 43003
- SQL: `sql/analytics.sql`
- Executed notebook: `notebooks/analysis.ipynb`
- API contract and implementation artifacts: `docs/`

No real customer, endpoint, token, employer workflow or confidential information is included.
