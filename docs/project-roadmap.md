# Portfolio Project Roadmap

## Prioritization Principles

Projects are ranked by how directly they prove Andrej's real combination of analytics support, technical troubleshooting, project delivery, product ownership, documentation, and governance. A smaller set of complete, inspectable projects is more credible than a large gallery of shallow dashboards.

Scoring language:

- Portfolio value: ability to change a hiring decision.
- Relevance: fit with Andrej's documented experience.
- Complexity: implementation and validation effort.
- Credibility risk: chance that the project implies unsupported production impact or proprietary access.

## Roadmap

| Project | Portfolio value | Relevance to Andrej | Complexity | Required data | Required tools | Estimated implementation phase | Status | Credibility risk | Recommended priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OpsDesk case study | Very high | Directly proves SupportOps, project delivery, ticketing, decisions, blockers, and reporting | Medium | Existing local app behavior; original demo records only | HTML, CSS, JavaScript, localStorage, SheetJS | Phase 1 | Existing app; case study selected | Low if described as a portfolio tool | P0 |
| SyncDesk case study | Very high | Directly proves analytics support, data governance, documentation, change history, and ownership | Medium | Existing local app behavior; original demo connections only | HTML, CSS, JavaScript, localStorage, SheetJS | Phase 1 | Existing app; case study selected | Low if no employer data is used | P0 |
| C. GA4 Data Quality Monitor | Very high | Closely matches analytics support, QA, discrepancy analysis, APIs, dashboards, and root-cause work | Medium | Original synthetic GA4-style events, transactions, UTMs, countries, and expected totals | SQL-style checks, JavaScript, CSV/JSON, dashboard UI | Phase 2 | Selected for implementation | Low with explicit synthetic labels | P1 |
| D. Analytics Change Control | Very high | Proves project management, product ownership, SLA thinking, acceptance criteria, QA, approvals, and release notes | Medium | Original synthetic change requests and delivery events | HTML, CSS, JavaScript, CSV/JSON, governance model | Phase 2 | Selected for implementation | Low if framed as a designed operating system | P1 |
| A. Marketing Analytics Command Center | High | Matches GA4, BigQuery, Datorama, paid media, CRM, taxonomy, and stakeholder reporting | High | Original synthetic GA4, Google Ads-style, Meta Ads-style, CRM, and taxonomy tables | SQL-style transformations, JavaScript, CSV/JSON, dashboard UI | Phase 3 | Selected for implementation | Medium; avoid claiming real campaign performance | P1 |
| H. Analytics Architecture Case Study | High | Matches APIs, Excel/CSV ingestion, BigQuery, semantic logic, QA, governance, and monitoring | Medium | No records required; original architecture and definitions | Original diagrams, HTML/CSS, data contracts | Phase 4 | Backlog; can be integrated into SyncDesk narrative | Low | P2 |
| G. Executive KPI Health Dashboard | Medium-high | Supports stakeholder reporting and action-oriented KPI ownership | Medium | Synthetic target, actual, trend, risk, and owner tables | JavaScript, CSV/JSON, accessible charts | Phase 4 | Backlog | Low | P2 |
| B. E-commerce Revenue Dashboard | Medium-high | Relevant to eCommerce delivery, retailer data, reconciliation, and monthly ingestion | High | Synthetic multi-retailer orders, FX rates, products, and reconciliation totals | SQL-style transformations, Python optional, CSV/JSON, dashboard UI | Phase 5 | Backlog | Medium; employer similarity must be avoided | P3 |
| E. Customer Segmentation | Medium | Shows business analysis but is less distinctive than SupportOps and analytics QA | Medium | Properly licensed public dataset or synthetic customer orders | Python or JavaScript, RFM, cohorts, optional k-means | Phase 5 | Backlog | Medium; avoid overstating ML sophistication | P3 |
| F. Forecasting and Scenario Planning | Medium | Useful analytics proof but less connected to current support and delivery positioning | High | Licensed or synthetic time series with seasonality and holdout period | Python, transparent baseline, error metrics, intervals | Phase 6 | Backlog | High if presented without robust validation | P4 |

## Selected Portfolio for This Redesign

### Flagship application category

1. OpsDesk
2. SyncDesk

These remain first and visually dominant. They are working products with everyday utility, not dashboard mockups.

### Analytics systems category

1. GA4 Quality Monitor
2. Analytics Change Control
3. Marketing Analytics Command Center

These support the flagship narrative instead of competing with it. Together they show detect, govern, deliver:

- Detect data-quality failures.
- Govern definitions and changes.
- Deliver decision-ready analytics.

## Data Plan

| Project | Data origin | Public label | Privacy rule |
| --- | --- | --- | --- |
| OpsDesk | User-created browser data; optional original demo records | Local-first application data | Never include user workspace exports in the repository |
| SyncDesk | User-created browser data; optional original demo records | Local-first application data | Never include real connection names, credentials, or employer schemas |
| GA4 Quality Monitor | Generated synthetic events and expected-results tables | Synthetic portfolio dataset | No real user IDs, domains, revenue, or employer taxonomy |
| Analytics Change Control | Generated synthetic requests, SLAs, QA checks, and release events | Synthetic operating dataset | No real tickets, stakeholders, or project names |
| Marketing Command Center | Generated synthetic media, web, CRM, and taxonomy extracts | Synthetic portfolio dataset | No real campaign, spend, revenue, customer, or employer records |

## Quality Gates Per Project

Every selected project must include:

1. A literal problem statement.
2. Andrej's role in the project.
3. Data origin and privacy statement.
4. Decision or operating model.
5. One original inspectable visual.
6. Method or implementation details.
7. Validation checks and known limitations.
8. Technology list tied to actual use.
9. A dedicated URL.
10. No unsupported production claim.

## Future Expansion Rule

Do not add another project until it has a stronger artifact, validation story, or hiring signal than the weakest existing case study. Depth remains the governing constraint.
