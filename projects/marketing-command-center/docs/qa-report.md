# QA report

- **PASS** — All four planned discount bands are represented: 4 bands
- **PASS** — Daily sales grain is unique: 139,776 rows; 0 duplicates
- **PASS** — Dashboard and SQL totals agree: Exact to €0.01
- **PASS** — Discount depth is not confounded with one execution mechanic: 4 mechanics represented in every discount band
- **PASS** — Every sales slice has one budget and locked forecast: 4,608 matched slices
- **PASS** — Forecast is locked before each reporting month: 0 invalid lock dates
- **PASS** — Net revenue formula reconciles: 0 rows outside €0.01 tolerance
- **PASS** — Promotion dates are valid: 0 invalid windows
- **PASS** — Returns never exceed gross units: 0 violations
