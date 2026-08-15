#!/usr/bin/env python3
"""Generate Andrej Glavnik's one-page, two-column portfolio CVs."""

from __future__ import annotations

import argparse
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


PAGE_W, PAGE_H = A4
BLUE = HexColor("#0b3b8f")
LINK_BLUE = HexColor("#1266d6")
PALE_BLUE = HexColor("#eaf3ff")
INK = HexColor("#111827")
MUTED = HexColor("#536174")

SITE_URL = "https://andrejglavnik.github.io"
LINKEDIN_URL = "https://www.linkedin.com/in/andrejglavnik/"
OPSDESK_URL = f"{SITE_URL}/projects/opsdesk/"
SYNCDESK_URL = f"{SITE_URL}/projects/syncdesk/"
RELIABILITY_URL = f"{SITE_URL}/projects/ga4-quality-monitor/"
INTEGRATION_URL = f"{SITE_URL}/projects/analytics-change-control/"
COMMERCIAL_URL = f"{SITE_URL}/projects/marketing-command-center/"


def wrap(text: str, font: str, size: float, width: float) -> list[str]:
    """Wrap text to a fixed width without adding non-ASCII hyphens."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if stringWidth(candidate, font, size) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    *,
    font: str = "Helvetica",
    size: float = 8.0,
    leading: float = 9.8,
    color=INK,
) -> float:
    c.setFillColor(color)
    c.setFont(font, size)
    for line in wrap(text, font, size, width):
        c.drawString(x, y, line)
        y -= leading
    return y


def draw_section(c: canvas.Canvas, title: str, x: float, y: float) -> float:
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 9.6)
    c.drawString(x, y, title.upper())
    return y - 12.6


def draw_bullets(
    c: canvas.Canvas,
    bullets: list[str],
    x: float,
    y: float,
    width: float,
    *,
    size: float = 7.8,
    leading: float = 9.35,
    gap: float = 2.1,
) -> float:
    for text in bullets:
        lines = wrap(text, "Helvetica", size, width - 10.5)
        c.setFillColor(BLUE)
        c.circle(x + 2.2, y + 2.1, 1.2, stroke=0, fill=1)
        c.setFillColor(INK)
        c.setFont("Helvetica", size)
        for line in lines:
            c.drawString(x + 8.8, y, line)
            y -= leading
        y -= gap
    return y


def draw_role(
    c: canvas.Canvas,
    title: str,
    company_line: str,
    tools: str,
    bullets: list[str],
    x: float,
    y: float,
    width: float,
) -> float:
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 9.65)
    for line in wrap(title, "Helvetica-Bold", 9.65, width):
        c.drawString(x, y, line)
        y -= 11.15

    c.setFillColor(LINK_BLUE)
    c.setFont("Helvetica-Bold", 7.55)
    c.drawString(x, y + 0.7, company_line)
    y -= 9.8

    c.setFillColor(MUTED)
    c.setFont("Helvetica-Bold", 7.25)
    for line in wrap(f"Tools: {tools}", "Helvetica-Bold", 7.25, width):
        c.drawString(x, y, line)
        y -= 8.65
    y -= 1.5

    y = draw_bullets(c, bullets, x, y, width, size=7.75, leading=9.25, gap=2.0)
    return y - 4.1


def draw_labeled_item(
    c: canvas.Canvas,
    title: str,
    detail: str,
    x: float,
    y: float,
    width: float,
    *,
    title_size: float = 7.7,
    detail_size: float = 7.25,
) -> float:
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", title_size)
    for line in wrap(title, "Helvetica-Bold", title_size, width):
        c.drawString(x, y, line)
        y -= 8.9
    c.setFillColor(MUTED)
    c.setFont("Helvetica", detail_size)
    for line in wrap(detail, "Helvetica", detail_size, width):
        c.drawString(x, y, line)
        y -= 8.55
    return y - 3.4


def draw_projects(c: canvas.Canvas, x: float, y: float, width: float) -> float:
    """Draw all five portfolio projects as compact, individually linked entries."""
    font = "Helvetica-Bold"
    size = 7.35
    leading = 9.0

    c.setFillColor(LINK_BLUE)
    c.setFont(font, size)
    c.drawString(x, y, "OpsDesk")
    ops_width = stringWidth("OpsDesk", font, size)
    c.linkURL(OPSDESK_URL, (x, y - 1.5, x + ops_width, y + 7.5), relative=0)
    separator_x = x + ops_width + 7
    c.setFillColor(MUTED)
    c.drawString(separator_x, y, "|")
    sync_x = separator_x + 8
    c.setFillColor(LINK_BLUE)
    c.drawString(sync_x, y, "SyncDesk")
    sync_width = stringWidth("SyncDesk", font, size)
    c.linkURL(SYNCDESK_URL, (sync_x, y - 1.5, sync_x + sync_width, y + 7.5), relative=0)
    y -= leading

    analytics_projects = [
        ("Analytics Reliability & Release Control", RELIABILITY_URL),
        ("SaaS Implementation & Integration Health", INTEGRATION_URL),
        ("Commercial Performance & Promotion Intelligence", COMMERCIAL_URL),
    ]
    for title, url in analytics_projects:
        c.setFillColor(LINK_BLUE)
        c.setFont(font, size)
        c.drawString(x, y, title)
        title_width = stringWidth(title, font, size)
        if title_width > width:
            raise ValueError(f"Project title exceeds CV column width: {title}")
        c.linkURL(url, (x, y - 1.5, x + title_width, y + 7.5), relative=0)
        y -= leading

    return y


def summary_for(variant: str) -> str:
    if variant == "data-analytics":
        return (
            "Data analytics and BI delivery professional with 3+ years across reporting, data integrations, "
            "technical support, and cross-functional operations. I turn business questions into governed KPIs, "
            "reliable dashboards, traceable data workflows, and decision-ready reporting through SQL, APIs, QA, "
            "root-cause analysis, and clear documentation."
        )
    return (
        "Technical project and product operations professional with 3+ years across analytics delivery, "
        "product ownership, technical support, data integrations, and customer-facing operations. I make "
        "complex data and support operations reliable, usable, and ready to scale through clear priorities, "
        "strong documentation, cross-functional ownership, and measurable business outcomes."
    )


def build_pdf(output_path: str | Path, variant: str = "main") -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=A4)
    c.setTitle("Andrej Glavnik CV")
    c.setAuthor("Andrej Glavnik")
    c.setCreator("Andrej Glavnik CV generator")
    subject = (
        "Data analytics, business intelligence, integrations, and technical support"
        if variant == "data-analytics"
        else "Technical project management, analytics, product ownership, and support operations"
    )
    c.setSubject(subject)

    left_x = 27
    right_x = 326
    left_w = 284
    right_w = PAGE_W - right_x - 22

    c.setFillColor(PALE_BLUE)
    c.rect(right_x - 9, 24, PAGE_W - right_x - 13, PAGE_H - 92, stroke=0, fill=1)

    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 25)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 32, "ANDREJ GLAVNIK")

    bar_y = PAGE_H - 58
    c.setFillColor(BLUE)
    c.rect(20, bar_y, PAGE_W - 40, 16, stroke=0, fill=1)
    contact = (
        "andrejglavnik.github.io  |  andrejglavnik1@gmail.com  |  "
        "linkedin.com/in/andrejglavnik  |  +381 603456146"
    )
    c.setFillColor(white)
    c.setFont("Helvetica", 7.1)
    c.drawCentredString(PAGE_W / 2, bar_y + 5.3, contact)
    c.linkURL(SITE_URL, (112, bar_y, 216, bar_y + 16), relative=0)
    c.linkURL("mailto:andrejglavnik1@gmail.com", (217, bar_y, 337, bar_y + 16), relative=0)
    c.linkURL(LINKEDIN_URL, (338, bar_y, 469, bar_y + 16), relative=0)

    y = PAGE_H - 78
    y = draw_section(c, "Summary", left_x, y)
    y = draw_wrapped(c, summary_for(variant), left_x, y, left_w, size=8.4, leading=10.35) - 6.5

    y = draw_section(c, "Work Experience", left_x, y)
    roles = [
        (
            "Lead Data Project Manager, Analytics & Business Intelligence",
            "Danone | Dec 2025 - Present",
            "Jira, Asana, Confluence, SFMC Intelligence, GA4, BigQuery, GTM, Looker Studio, APIs, AWS S3",
            [
                "Own analytics and SFMC Intelligence priorities across dashboards, reporting workflows, data quality, stakeholder requests, and delivery follow-through.",
                "Translate business needs into product requirements, acceptance context, KPI logic, and data-quality workflows.",
                "Coordinate discovery, prioritization, QA, release readiness, handoffs, and adoption across business and technical teams.",
                "Own delivery across dashboards, API and spreadsheet pipelines, tagging QA, retailer sources, and documentation.",
                "Scope expanded from project delivery into product-ownership responsibilities after six months, coordinating 10+ cross-functional groups.",
            ],
        ),
        (
            "Software Support Engineer L2, Data & Integrations",
            "Databox | Mar 2025 - Dec 2025",
            "SQL, Postman, BigQuery, MySQL, Redshift, Snowflake, GA4, HubSpot, Zendesk, Intercom",
            [
                "Delivered upper-tier analytics and BI support for dashboards, connectors, APIs, SQL/database sources, and metric-sync issues.",
                "Debugged API connections, ETL flows, calculated metrics, data discrepancies, and dashboard interpretation.",
                "Prepared reproducible escalations connecting customers, support, product, and engineering on complex cases.",
                "Led knowledge sharing and process improvements cited in a dedicated recommendation from the Director of Support.",
            ],
        ),
        (
            "Business Development Specialist, Sales and UX",
            "Databox | Apr 2024 - Mar 2025",
            "HubSpot, Intercom, Slack, Zoom, MEDDPICC, BANT, discovery, product education",
            [
                "Qualified 150+ inbound and outbound leads per month through chat, email, discovery, and product education.",
                "Scheduled 100+ product demos per month with a 30% demo-to-opportunity conversion rate.",
                "Influenced $50K+ in pipeline and contributed to $50K in closed revenue through high-quality handoffs.",
                "Connected customer needs with product value, onboarding, support context, and platform adoption.",
            ],
        ),
        (
            "Senior Technical Support Engineer, NOC (L3)",
            "Walmart | May 2023 - Apr 2024",
            "ServiceNow, Citrix, Cisco Jabber, PowerShell, Linux, Cisco, Meraki, Juniper, NCR, POS",
            [
                "Supported Walmart US and Sam's Club US network infrastructure, POS systems, and enterprise hardware.",
                "Diagnosed network, software, hardware, and connectivity issues across high-pressure retail environments.",
                "Coordinated dispatch, repair follow-up, ticket quality, documentation, and operational continuity.",
                "Built the networking and troubleshooting foundation behind later analytics and support operations work.",
            ],
        ),
    ]
    for title, company_line, tools, bullets in roles:
        y = draw_role(c, title, company_line, tools, bullets, left_x, y, left_w)

    ry = PAGE_H - 78
    ry = draw_section(c, "Professional Proof", right_x, ry)
    proof = [
        "Supported customers across a platform ecosystem offering 300+ data-source, connector, and integration types.",
        "$100K+ in ARR and pipeline influenced through qualification, demos, and high-quality handoffs.",
        "13+ LinkedIn recommendations from managers, a CEO, mentors, peers, and collaborators.",
        "Dedicated recommendation from Databox's Director of Support based on direct management experience.",
        "Scope expanded from project delivery into product-ownership responsibilities after six months.",
    ]
    ry = draw_bullets(c, proof, right_x, ry, right_w, size=7.7, leading=9.2, gap=1.95) - 3.0

    ry = draw_section(c, "Education", right_x, ry)
    education = [
        (
            "ITAcademy by LINKgroup",
            "Specialization: Web Project Manager & Data Analyst, In progress, Jul 2026 - Apr 2027 (expected)",
        ),
        (
            "ITS - Higher Education Institution for Information Technologies",
            "Bachelor of Applied Studies in Digital Business, 2023 - Present",
        ),
        (
            "ITAcademy by LINKgroup",
            "Certified QA Engineer and Software Testing Specialist, Oct 2024 - Dec 2025",
        ),
        (
            "ITAcademy by LINKgroup",
            "Certified Network and System Administration, Aug 2023 - Oct 2024",
        ),
    ]
    for title, detail in education:
        ry = draw_labeled_item(c, title, detail, right_x, ry, right_w)

    ry = draw_section(c, "Tools & Platforms", right_x, ry + 0.5)
    tool_groups = [
        "Delivery: Jira, Asana, Confluence, ServiceNow, Slack, GitHub, DevOps",
        "Analytics: GA4, GTM, BigQuery, Datorama / SFMC Intelligence, Looker Studio",
        "Data: SQL, REST APIs, Postman, AWS S3, CSV/XLS, MySQL, Redshift, Snowflake",
        "Customer: HubSpot, Intercom, Zendesk, Freshdesk, Salesforce, Shopify, Stripe",
        "Marketing: Google Ads, Meta Ads, LinkedIn Ads, Amazon Ads, Vendor Central",
        "Infrastructure: Citrix, Cisco Jabber, PowerShell, Linux, Cisco, Meraki, Juniper",
        "Methods: KPI governance, QA, root-cause analysis, MEDDPICC, BANT, documentation",
    ]
    ry = draw_bullets(c, tool_groups, right_x, ry, right_w, size=7.4, leading=8.75, gap=1.55) - 2.6

    ry = draw_section(c, "Certificates", right_x, ry)
    certificates = [
        "Certified QA Engineer & Software Tester - ITAcademy, 2025",
        "Certified Computer Network Administrator - ITAcademy, 2024",
        "CCNA Routing and Switching - ITAcademy",
        "LPIC-1 Linux Administrator - ITAcademy",
        "MikroTik Certified Network Associate - ITAcademy",
        "ISO/IEC 27001 Information Security Associate - SkillFront",
        "Scrum Foundation Professional Certificate - CertiProf",
        "Google Analytics for Businesses - Google",
        "HubSpot Inbound Sales & Marketing - HubSpot",
        "Generative AI Fundamentals - Databricks",
        "Zendesk Customer Service Professional - Zendesk",
        "CompTIA Network+ - ITAcademy",
        "Career Essentials in Cybersecurity - Microsoft",
        "Career Essentials in GitHub Professional Certificate - GitHub",
    ]
    ry = draw_bullets(c, certificates, right_x, ry, right_w, size=7.2, leading=8.2, gap=1.1) - 2.5

    ry = draw_section(c, "Key Skills", right_x, ry)
    key_skills = [
        "Product ownership and roadmap prioritization",
        "Technical project management and delivery",
        "Stakeholder alignment and requirements clarification",
        "Analytics delivery, KPI governance, and dashboard QA",
        "Data quality, integrations, and root-cause analysis",
        "Technical support and escalation management",
        "Process improvement and operational documentation",
        "Customer success, discovery, demos, and sales handoffs",
        "Cross-functional leadership across product, support, analytics, and DevOps",
        "Knowledge-base ownership and technical communication",
    ]
    ry = draw_bullets(c, key_skills, right_x, ry, right_w, size=7.2, leading=8.2, gap=1.1) - 2.5

    ry = draw_section(c, "Projects", right_x, ry)
    ry = draw_projects(c, right_x, ry, right_w)

    # Fail loudly during generation if future content silently overflows the page.
    if y < 24 or ry < 24:
        raise ValueError(f"CV content overflow: left={y:.1f}, right={ry:.1f}")

    c.save()
    print(output_path)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output",
        nargs="?",
        default="assets/Andrej-Glavnik-CV.pdf",
        help="Output PDF path",
    )
    parser.add_argument(
        "--variant",
        choices=("main", "data-analytics"),
        default="main",
        help="CV positioning variant",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build_pdf(args.output, variant=args.variant)
