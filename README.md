# Andrej Glavnik Portfolio Website

Static GitHub Pages portfolio for Andrej Glavnik, focused on technical project management, customer-facing operations, analytics delivery, technical support, product ownership, certifications, recommendation proof and practical workflow tooling.

The repository also includes **OpsDesk**, a functional local-first daily operations workbench. It combines task capture, priority and status management, technical context, blockers, meeting notes, decision logging, automatic team updates, archive recovery, and JSON/CSV backup in a single browser application.

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

No build step is required. OpsDesk stores workspace data in the user's browser and does not send it to a backend.
