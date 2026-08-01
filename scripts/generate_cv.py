#!/usr/bin/env python3
"""Generate Andrej Glavnik's one-page portfolio CV."""

from pathlib import Path
import sys

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


def wrap(text, font, size, width):
    words = text.split()
    lines = []
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


def draw_wrapped(c, text, x, y, width, font="Helvetica", size=7.15,
                 leading=8.8, color=INK):
    c.setFillColor(color)
    c.setFont(font, size)
    for line in wrap(text, font, size, width):
        c.drawString(x, y, line)
        y -= leading
    return y


def draw_section(c, title, x, y):
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 8.25)
    c.drawString(x, y, title.upper())
    return y - 11.5


def draw_bullets(c, bullets, x, y, width, size=7.0, leading=8.35, gap=2.15):
    for text in bullets:
        lines = wrap(text, "Helvetica", size, width - 10)
        c.setFillColor(BLUE)
        c.circle(x + 2.2, y + 1.9, 1.15, stroke=0, fill=1)
        c.setFillColor(INK)
        c.setFont("Helvetica", size)
        for line in lines:
            c.drawString(x + 8.5, y, line)
            y -= leading
        y -= gap
    return y


def draw_role(c, title, company_line, tools, bullets, x, y, width):
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 9.4)
    for line in wrap(title, "Helvetica-Bold", 9.4, width):
        c.drawString(x, y, line)
        y -= 10.9

    c.setFillColor(LINK_BLUE)
    c.setFont("Helvetica-Bold", 6.65)
    c.drawString(x, y + 0.7, company_line)
    y -= 8.7

    c.setFillColor(MUTED)
    c.setFont("Helvetica-Bold", 6.4)
    tool_lines = wrap(f"Tools: {tools}", "Helvetica-Bold", 6.4, width)
    for line in tool_lines:
        c.drawString(x, y, line)
        y -= 7.7
    y -= 1.4

    y = draw_bullets(c, bullets, x, y, width, size=7.0, leading=8.35, gap=1.9)
    return y - 4.0


def draw_labeled_item(c, title, detail, x, y, width):
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 7.2)
    for line in wrap(title, "Helvetica-Bold", 7.2, width):
        c.drawString(x, y, line)
        y -= 8.25
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 6.35)
    for line in wrap(detail, "Helvetica", 6.35, width):
        c.drawString(x, y, line)
        y -= 7.45
    return y - 4.1


def build_pdf(output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=A4)
    c.setTitle("Andrej Glavnik CV")
    c.setAuthor("Andrej Glavnik")
    c.setSubject("Technical project management, product ownership, analytics, and support operations")

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
    c.rect(20, bar_y, PAGE_W - 40, 15, stroke=0, fill=1)
    contact = "andrejglavnik.github.io  |  andrejglavnik1@gmail.com  |  linkedin.com/in/andrejglavnik  |  +381 603456146"
    c.setFillColor(white)
    c.setFont("Helvetica", 6.15)
    c.drawCentredString(PAGE_W / 2, bar_y + 5.0, contact)
    c.linkURL("https://andrejglavnik.github.io", (125, bar_y, 215, bar_y + 15), relative=0)
    c.linkURL("mailto:andrejglavnik1@gmail.com", (218, bar_y, 333, bar_y + 15), relative=0)
    c.linkURL("https://www.linkedin.com/in/andrejglavnik/", (338, bar_y, 455, bar_y + 15), relative=0)

    y = PAGE_H - 78
    y = draw_section(c, "Summary", left_x, y)
    summary = (
        "Technical project and product operations professional with 4+ years across analytics delivery, "
        "product ownership, technical support, data integrations, and customer-facing operations. I make "
        "complex data and support operations reliable, usable, and ready to scale through clear priorities, "
        "strong documentation, cross-functional ownership, and measurable business outcomes."
    )
    y = draw_wrapped(c, summary, left_x, y, left_w, size=7.5, leading=9.3) - 6.5

    y = draw_section(c, "Work Experience", left_x, y)
    roles = [
        (
            "Data Analytics Product Owner, Business Intelligence and Integrations",
            "Danone | Jun 2026 - Present",
            "Jira, Asana, Confluence, SFMC Intelligence, GA4, BigQuery, GTM, APIs, AWS S3",
            [
                "Own analytics priorities, backlog clarity, stakeholder alignment, reporting support, and cross-functional delivery.",
                "Translate business needs into product requirements, acceptance context, KPI logic, and data-quality workflows.",
                "Coordinate discovery, prioritization, QA, release readiness, handoffs, and adoption across business and technical teams.",
                "Promoted from project management scope into product ownership after six months, coordinating 10+ cross-functional groups.",
            ],
        ),
        (
            "Lead Data Project Manager, Analytics & Business Intelligence",
            "Danone | Dec 2025 - Jun 2026",
            "Datorama / SFMC Intelligence, GA4, BigQuery, GTM, Looker Studio, APIs, AWS S3, Jira",
            [
                "Led analytics delivery across websites, eCommerce, digital marketing, reporting support, and documentation.",
                "Structured KPI frameworks, tracking requirements, data standards, owners, blockers, and vendor coordination.",
                "Owned delivery across dashboards, API and spreadsheet pipelines, tagging QA, and retailer data sources.",
                "Drove root-cause analysis and built centralized KPI, mapping, troubleshooting, and onboarding documentation.",
            ],
        ),
        (
            "Technical Software Support Engineer L2, Data & Integrations",
            "Databox | Mar 2025 - Dec 2025",
            "SQL, Postman, BigQuery, MySQL, Redshift, Snowflake, GA4, HubSpot, Zendesk, Intercom",
            [
                "Delivered upper-tier analytics and BI support for dashboards, connectors, APIs, SQL/database sources, and metric sync issues.",
                "Debugged API connections, ETL flows, calculated metrics, data discrepancies, and dashboard interpretation.",
                "Prepared reproducible escalations connecting customers, support, product, and engineering on complex cases.",
                "Led knowledge sharing and process improvements cited in a dedicated recommendation from the Director of Support.",
            ],
        ),
        (
            "Business Development Specialist, Sales & Customer Success",
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
    ry = draw_section(c, "Education", right_x, ry)
    education = [
        (
            "ITAcademy by LINKgroup",
            "Specialization: Web Project Manager & Data Analyst, Jul 2026 - Apr 2027 (expected)",
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

    ry = draw_section(c, "Tools & Platforms", right_x, ry + 1)
    tool_groups = [
        "Delivery: Jira, Asana, Confluence, ServiceNow, Slack, GitHub, DevOps",
        "Analytics: GA4, GTM, BigQuery, Datorama / SFMC Intelligence, Looker Studio",
        "Data: SQL, REST APIs, Postman, AWS S3, CSV/XLS, MySQL, Redshift, Snowflake",
        "Customer: HubSpot, Intercom, Zendesk, Freshdesk, Salesforce, Shopify, Stripe",
        "Marketing: Google Ads, Meta Ads, LinkedIn Ads, Amazon Ads, Vendor Central",
        "Infrastructure: Citrix, Cisco Jabber, PowerShell, Linux, Cisco, Meraki, Juniper",
        "Methods: KPI governance, QA, root-cause analysis, MEDDPICC, BANT, documentation",
    ]
    ry = draw_bullets(c, tool_groups, right_x, ry, right_w, size=6.55, leading=7.8, gap=1.9) - 3

    ry = draw_section(c, "Professional Proof", right_x, ry)
    proof = [
        "300+ data-source, connector, and integration types supported across analytics and business systems.",
        "$100K+ in ARR and pipeline influenced through qualification, demos, and high-quality handoffs.",
        "13+ LinkedIn recommendations from managers, a CEO, mentors, peers, and collaborators.",
        "Dedicated recommendation from Databox's Director of Support based on direct management experience.",
        "Promoted from project management scope into product ownership after six months.",
    ]
    ry = draw_bullets(c, proof, right_x, ry, right_w, size=6.55, leading=7.85, gap=2.0) - 3

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
    ry = draw_bullets(c, certificates, right_x, ry, right_w, size=6.1, leading=7.1, gap=1.3) - 3

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
    draw_bullets(c, key_skills, right_x, ry, right_w, size=6.1, leading=7.15, gap=1.35)

    c.save()
    print(output_path)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "assets/Andrej-Glavnik-CV.pdf"
    build_pdf(target)
