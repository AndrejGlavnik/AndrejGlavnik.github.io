# Liquid Glass Portfolio Redesign Proposal

## 1. Executive Summary

The redesign will reposition Andrej Glavnik's site as a concise analytics delivery and technical project management portfolio. It will preserve the existing one-page order, real experience, recommendations, certifications, and runnable OpsDesk/SyncDesk applications while replacing the current long card wall with a calmer workspace-like interface.

The result will remain a dependency-light static site suitable for GitHub Pages. The public interface will use an original, macOS-influenced surface system with restrained translucency, clear fallbacks, real product visuals, dedicated project URLs, and short evidence-led copy.

## 2. Current-Site Assessment

- Framework: static semantic HTML, CSS, and vanilla JavaScript.
- Build system: none; files are served directly.
- Deployment: GitHub Pages from `main` and `/root`, protected by `.nojekyll`.
- Main entry point: `index.html`.
- Public application routes: `/projects/opsdesk/` and `/projects/syncdesk/`.
- Legacy routes: redirect pages for blog, book, case studies, certificates, CV, projects, recommendations, and services.
- Dependencies: a vendored SheetJS browser build used by the project apps; no package manager or runtime dependency.
- Client storage: theme preferences and the shared local-first app workspace use `localStorage`.
- Current visual validation: no console errors at 1440px or 390px; horizontal overflow exists at 390px.
- Current SEO: homepage Person JSON-LD and basic Open Graph metadata exist; canonical links, project CreativeWork data, full sitemap coverage, and raster social previews are missing.

## 3. Content Inventory

| Area | Existing content | Decision |
| --- | --- | --- |
| Hero | Name, professional positioning, short operating promise, CV, LinkedIn, work-mode labels | Preserve facts, tighten language, improve visual proof |
| Impact | Eight metrics and proof points | Keep the strongest verified metrics; reduce first-screen density |
| Proof | Experience, recommendations, director letter, credentials | Preserve and present as an evidence strip |
| Experience | Five roles with tools, responsibilities, and achievements | Preserve all accurate content; use a compact timeline and progressive disclosure |
| Recommendations | Featured director recommendation and twelve additional recommendations | Preserve full proof, feature two, collapse the full archive |
| Credentials | Twelve LinkedIn-listed certifications | Preserve; group by capability instead of twelve equal cards |
| Tools | Six broad categories | Preserve categories; remove badge-wall behavior |
| Builds | OpsDesk and SyncDesk runnable tools | Make the primary portfolio category and keep above analytics case studies |
| Contact | Email, CV, GitHub, LinkedIn | Keep one primary action and compact secondary links |
| Assets | CV, director letter, current product previews, favicon, social card | Preserve valid files; create original redesigned previews and metadata assets |

## 4. Existing Design Strengths

- Clear one-page section order.
- Accurate, work-focused positioning.
- Strong recommendation evidence.
- Real runnable projects rather than static mockups.
- Existing light and dark modes.
- Low dependency and fast static delivery.
- Semantic section headings and native `details` controls.
- Consistent blue accent and compact top navigation.

## 5. Existing Design Weaknesses

- The homepage is visually repetitive because most information is placed in equal white cards.
- The mobile layout has horizontal overflow.
- Recommendations and certificates produce an unnecessarily long page.
- OpsDesk and SyncDesk arrive late and visually resemble ordinary cards despite being the strongest proof.
- The hero's eight-metric panel competes with Andrej's positioning.
- The current project section lacks dedicated case-study routes and a clear distinction between applications and analytics studies.
- Light mode reads as a single pale-blue family; dark mode reads as a single dark-slate family.
- Social metadata uses an SVG rather than a widely compatible optimized raster image.
- Sitemap coverage is incomplete.

## 6. Proposed Visual Direction

The design will feel like a calm professional workspace, not a macOS imitation.

### Surface hierarchy

1. Environment: near-white or charcoal canvas with a subtle neutral texture.
2. Section surface: mostly unframed full-width bands with constrained content.
3. Elevated work preview: translucent panes used only for product and evidence previews.
4. Controls: compact glass buttons, segmented filters, and icon actions.
5. Temporary state: an accessible dialog or native disclosure only when it improves inspection.

### Tokens

- Neutral ink and paper as primary colors.
- System blue for navigation and primary actions.
- Mint for verified/current states.
- Amber for attention and data-quality warnings.
- Coral only for high-risk or failed checks.
- Maximum card radius: 8px.
- System font stack only; no external font requests.
- Motion durations between 140ms and 320ms, disabled under reduced-motion preferences.
- Blur limited to header, project preview surfaces, and temporary overlays.

### Visual signature

The signature element will be a real dual-product workspace in the hero: OpsDesk and SyncDesk screenshots composed as inspectable, layered application surfaces. The effect communicates Andrej's ability to build operational systems before the visitor reaches the project section.

## 7. Proposed Information Architecture

The homepage keeps the existing order:

1. Start page / Hero
2. Proof
3. Experience
4. Recommendations
5. Certificates
6. Tools
7. Builds
8. Contact

Within Builds:

1. Flagship applications: OpsDesk, then SyncDesk.
2. Analytics systems: selected original analytics case studies.

Dedicated URLs will support search, sharing, accessibility, and deeper review:

- `/projects/opsdesk/` existing runnable tool
- `/projects/opsdesk/case-study.html` project narrative
- `/projects/syncdesk/` existing runnable tool
- `/projects/syncdesk/case-study.html` project narrative
- `/projects/ga4-quality-monitor/`
- `/projects/marketing-command-center/`
- `/projects/analytics-change-control/`

## 8. Proposed Component Architecture

The site stays framework-free because migration would add build complexity without improving this scope.

| Component | Responsibility |
| --- | --- |
| Glass header | Identity, section navigation, theme toggle, CV action |
| Hero workspace | Positioning, two primary actions, real product visual |
| Proof rail | Four high-value evidence points with source context |
| Experience timeline | Company, role, period, summary, native expandable details |
| Recommendation stage | Two featured quotes and expandable full archive |
| Credential index | Grouped credential list with LinkedIn verification |
| Capability map | Tool categories mapped to operating outcomes |
| Flagship showcase | Large OpsDesk and SyncDesk previews with live and case-study actions |
| Analytics project index | Original case studies with category, problem, stack, visual, and objective |
| Case-study shell | Shared hero, decision summary, process, evidence, validation, data origin |
| Theme controller | Stored light/dark preference with system preference fallback |
| Navigation observer | Active section state without layout changes |

Shared styling will live in `assets/css/styles.css` and `assets/css/case-study.css`. Shared behavior will remain in small vanilla JavaScript files. Public content will remain rendered in HTML for SEO and no-JavaScript readability.

## 9. Proposed Project Portfolio

### Flagship applications

1. **OpsDesk**: local-first daily operations workbench. Preserve the existing functional application and add a concise case study around capture, prioritization, blockers, reporting, backups, and privacy.
2. **SyncDesk**: local-first data connection knowledge workspace. Preserve the existing functional application and add a case study around ownership, schema, calculations, manifest history, discrepancies, and shared backups.

### Selected original analytics systems

1. **GA4 Quality Monitor**: synthetic event and transaction dataset, deterministic QA checks, issue triage, and dashboard reconciliation.
2. **Marketing Command Center**: synthetic GA4, paid-media, and CRM extracts harmonized through an original campaign taxonomy and KPI layer.
3. **Analytics Change Control**: an original delivery-governance case study connecting intake, priority, SLA, acceptance criteria, QA, approvals, and release notes.

These three cover Andrej's differentiator: analytics support, delivery governance, and project ownership. Additional forecasting and segmentation projects are lower priority because they would broaden the portfolio without strengthening this narrative as much.

## 10. Reference-Derived Ideas

- Harrison Jansma: put runnable flagship work before secondary projects and keep outcomes next to the artifact.
- Yan Holtz: let the interface demonstrate analytical judgment and connect projects to live outputs.
- Naledi Hollbruegge: describe capability as a sequence of useful business actions.
- Tim Hopper: use documentation-like clarity and labels without adopting the dense blog layout.
- Jessie-Raye Bauer: give substantial projects a strong visual and dedicated route.
- Anubhav Gupta: state Andrej's role on each case study.
- Maggie Wolff: connect the career narrative across customer communication and analytics.
- Neil Martinez: use a short, outcome-led opening and disciplined whitespace.
- Ger Inberg: separate project categories when that improves scanning.
- James Le: provide direct source and artifact links, but add validation and decision context.
- Muhammad Gardian Novandri and the Figma reference: preserve clear identity and section discoverability while rejecting the template treatment.

## 11. Elements Intentionally Rejected

- Skill percentages and proficiency bars.
- Full-screen stock photography.
- Decorative operating-system controls.
- Large portrait-led hero.
- Cursor followers, animated particles, and constant floating motion.
- Deep blog navigation and unrelated personal pages.
- Equal-card grids for every section.
- Repetition of the same CTA.
- Third-party projects or screenshots relabelled as Andrej's work.

## 12. Data and Copyright Considerations

- All new analytics datasets will be generated specifically for this portfolio and clearly labelled synthetic.
- Synthetic company, campaign, product, and user identifiers will not encode real employer information.
- No proprietary Danone, Databox, Walmart, customer, dashboard, ticket, metric, or system data will be used.
- Existing recommendation and career content remains Andrej's provided material.
- Existing SheetJS is already vendored for OpsDesk/SyncDesk; its upstream licence will be documented.
- No reference-site code, screenshots, imagery, copy, or project claims will be included in the public redesign.

## 13. Technical Implementation Plan

1. Preserve static hosting and existing application routes.
2. Refactor the homepage into semantic, reusable visual patterns.
3. Introduce CSS design tokens and explicit transparency fallbacks.
4. Keep native `details` for experience and recommendation archives.
5. Add original case-study routes with shared styles and small progressive enhancements.
6. Add synthetic CSV/JSON datasets and data dictionaries under project-specific `data/` folders.
7. Add raster WebP/PNG social and project preview images.
8. Improve canonical metadata, Open Graph data, Person/CreativeWork JSON-LD, sitemap, and robots coverage.
9. Validate links, console output, responsiveness, accessibility, reduced motion, no-backdrop support, and performance.
10. Store final preview screenshots and report under `docs/`.

There is no production build step. A production check therefore means serving the exact static files through a local HTTP server and validating every route as it will be hosted.

## 14. Backup and Rollback Status

- Original branch: `main`
- Original remote baseline: `8ce50e09f58d29c7fef73b9b63e3cf81383de1f4`
- Backup commit: `64b55bffa4d22998063a0e03302923360ac442b0`
- Backup tag: `pre-liquid-glass-redesign`
- Backup branch: `backup/original-portfolio`
- Redesign branch: `redesign/liquid-glass-portfolio`
- Source archive: `archive/original-site-before-redesign/`
- Production deployment status: unchanged and not redeployed.

## 15. Risks

| Risk | Mitigation |
| --- | --- |
| Glass effects reduce contrast | Limit blur, enforce opaque fallback, test both themes |
| New case studies look fabricated | Label data synthetic and frame outcomes as project objectives or observed dataset results |
| Homepage becomes long again | Use compact summaries and native progressive disclosure |
| App service workers cache old assets during review | Version assets and unregister/cache-bust in local validation when required |
| External links change | Validate before final review and report any inaccessible URL |
| Archive is accidentally served if deployed later | It is outside linked navigation and sitemap; deployment guidance can exclude it if desired |

## 16. Open Assumptions

- Existing professional claims and recommendation text are user-approved and accurate.
- Existing OpsDesk and SyncDesk functionality should not be rewritten unless required for integration or accessibility.
- The CV PDF remains the approved public CV.
- Public email, LinkedIn, GitHub, and company links remain valid.
- The redesign must remain English-language and recruiter-facing.
- Final deployment will occur only after Andrej explicitly approves the local preview.

## 17. Definition of Done

- Original site is recoverable from branch, tag, commit, and archive.
- Homepage preserves required section order and accurate content.
- OpsDesk and SyncDesk remain functional and appear first in Builds.
- Three original analytics case studies have dedicated URLs, synthetic data, and data-origin notes.
- No public reference owner name, domain, copied asset, or copied project remains.
- No horizontal overflow at tested mobile, tablet, or desktop widths.
- Light, dark, reduced-motion, and reduced-transparency modes are readable.
- Keyboard focus and native disclosures work.
- All internal routes and required external links pass validation or are reported.
- No console errors occur on tested pages.
- SEO metadata, structured data, sitemap, robots, and social preview are complete.
- Preview screenshots and the final redesign report are available.
- Nothing is deployed or pushed to the GitHub Pages production branch.
