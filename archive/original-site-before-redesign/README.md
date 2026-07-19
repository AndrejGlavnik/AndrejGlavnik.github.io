# Andrej Glavnik Portfolio Website

Static GitHub Pages portfolio for Andrej Glavnik, focused on technical project management, customer-facing operations, analytics delivery, technical support, product ownership, certifications, recommendation proof and practical workflow tooling.

The repository also includes **OpsDesk**, a functional local-first daily operations workbench. It combines task capture, priority and status management, technical context, blockers, meeting notes, decision logging, automatic team updates, archive recovery, and JSON/CSV export in a single browser application. The complete JSON backup can be merged into or used to replace a workspace; CSV is intended for reporting rather than restoration.

## Live Site

https://andrejglavnik.github.io/

## Structure

- `index.html` - one-page technical project management portfolio
- `services.html` - legacy redirect to the work section
- `case-studies.html` - legacy redirect to proof
- `projects.html` - legacy redirect to projects
- `projects/opsdesk/` - installable daily operations workbench
- `projects/shared/` - shared local-first project UI and browser utilities
- `blog.html` - legacy redirect to projects
- `book.html` - legacy redirect to contact
- `recommendations.html` - legacy redirect to recommendations
- `assets/css/styles.css` - static design system
- `assets/js/main.js` - lightweight year/header behavior

## Positioning

The site positions Andrej as a technical project manager who can turn messy customer, support, analytics, ticketing and delivery problems into clear owned work.

## Deployment

This repository is designed to run directly through GitHub Pages:

1. Repository: `AndrejGlavnik.github.io`
2. Source: deploy from branch
3. Branch: `main`
4. Folder: `/root`

No build step is required. OpsDesk autosaves workspace data to the site's `localStorage` and does not send it to a backend. Clearing site data removes that browser copy, so the app explains the limitation on first use and provides a portable JSON backup/import workflow.
