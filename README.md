# Andrej Glavnik Portfolio

A static, one-page portfolio for technical project management, product ownership, analytics delivery, support operations, and customer-facing systems. The site includes two usable local-first browser products and three original analytics case studies with inspectable synthetic data.

## Local preview

No build step or package installation is required.

```bash
python3 -m http.server 4180 --bind 127.0.0.1
```

Open `http://127.0.0.1:4180/`.

## Public routes

- `/` - one-page portfolio
- `/projects/opsdesk/` - OpsDesk application
- `/projects/opsdesk/case-study.html` - OpsDesk product case study
- `/projects/syncdesk/` - SyncDesk application
- `/projects/syncdesk/case-study.html` - SyncDesk product case study
- `/projects/ga4-quality-monitor/` - analytics QA case study
- `/projects/analytics-change-control/` - analytics delivery governance case study
- `/projects/marketing-command-center/` - cross-channel marketing analytics case study

Legacy pages remain as redirects to the relevant one-page section.

## Project structure

- `index.html` - portfolio shell and content
- `assets/css/styles.css` - portfolio design system
- `assets/js/main.js` - theme, navigation, reveal, and experience behavior
- `assets/css/case-study.css` - shared case-study design system
- `assets/js/case-study.js` - shared case-study interactions
- `projects/opsdesk/` - installable daily operations workbench
- `projects/syncdesk/` - installable data-connection knowledge workspace
- `projects/*/data/` - synthetic, inspectable portfolio datasets and definitions
- `docs/` - reference research, redesign decisions, roadmap, QA, and handoff
- `archive/original-site-before-redesign/` - original production source preserved outside the active routes

## Local-first data

OpsDesk and SyncDesk save working data in the browser's `localStorage`. No backend, account, analytics tracker, or upload is used. Clearing site data removes the browser copy, so both applications provide a portable JSON workspace export and import flow. Human-readable Excel, CSV, and Markdown exports are reports; JSON is the complete restore format shared by both applications.

## Data and claims

The analytics projects use clearly labeled synthetic data created for this portfolio. They demonstrate methods, decisions, QA, and governance without exposing employer information or claiming production deployment. Employment and recommendation content is based on Andrej's supplied CV, LinkedIn material, and signed recommendation letter.

## Dependencies and licences

The portfolio uses system fonts and first-party HTML, CSS, JavaScript, screenshots, and synthetic data. OpsDesk and SyncDesk vendor SheetJS Community Edition for spreadsheet export. Attribution and licence details are recorded in [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md).

## Deployment

The repository is compatible with GitHub Pages from the repository root and requires no build output. Deployment is intentionally separate from local redesign work; review the local preview and `docs/final-redesign-report.md` before publishing.

Production site: https://andrejglavnik.github.io/
