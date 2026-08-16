#!/usr/bin/env python3
"""Fail fast when approved public-profile facts drift across tracked sources."""

from __future__ import annotations

import json
import re
from html import escape, unescape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = json.loads((ROOT / "data/profile.json").read_text(encoding="utf-8"))
WEBSITE_SOURCE = (ROOT / "index.html").read_text(encoding="utf-8")
WEBSITE_TEXT = unescape(WEBSITE_SOURCE)
CV_PATH = ROOT / "scripts/generate_cv.py"

if not CV_PATH.exists():
    raise SystemExit("Missing CV generator: scripts/generate_cv.py")

CV_SOURCE = CV_PATH.read_text(encoding="utf-8")


def require(label: str, needle: str, haystack: str) -> None:
    if needle not in haystack:
        raise SystemExit(f"Missing approved {label}: {needle}")


def require_once(label: str, needle: str, haystack: str) -> None:
    count = haystack.count(needle)
    if count != 1:
        raise SystemExit(f"Expected one approved {label}, found {count}: {needle}")


def forbid(label: str, needle: str, haystack: str) -> None:
    if needle in haystack:
        raise SystemExit(f"Unsafe or stale {label}: {needle}")


role_count = WEBSITE_SOURCE.count('class="role reveal"')
expected_role_count = PROFILE["experience"]["website_role_count"]
if role_count != expected_role_count:
    raise SystemExit(f"Expected {expected_role_count} website roles, found {role_count}")

json_ld_match = re.search(
    r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
    WEBSITE_SOURCE,
    re.DOTALL,
)
if not json_ld_match:
    raise SystemExit("Missing homepage JSON-LD")

json_ld = json.loads(json_ld_match.group(1))
people = [item for item in json_ld.get("@graph", []) if item.get("@type") == "Person"]
if len(people) != 1:
    raise SystemExit(f"Expected one Person in homepage JSON-LD, found {len(people)}")

current_title = PROFILE["experience"]["roles"][0]["title"]
if people[0].get("jobTitle") != current_title:
    raise SystemExit(
        f"JSON-LD jobTitle drift: expected {current_title}, found {people[0].get('jobTitle')}"
    )

for role in PROFILE["experience"]["roles"]:
    require_once("website role heading", f"<h3>{escape(role['title'])}</h3>", WEBSITE_SOURCE)
    require("CV role title", role["title"], CV_SOURCE)
    require("website role dates", role["dates"], WEBSITE_TEXT)
    require("CV role dates", role["dates"], CV_SOURCE)

require("experience", PROFILE["positioning"]["experience_years"], WEBSITE_TEXT)
require("experience", PROFILE["positioning"]["experience_years"], CV_SOURCE)
require("platform wording", PROFILE["approved_claims"]["platform_ecosystem_website"], WEBSITE_TEXT)
require("platform wording", PROFILE["approved_claims"]["platform_ecosystem_cv"], CV_SOURCE)
require("active program", PROFILE["education"]["program"], WEBSITE_TEXT)
require("active program", PROFILE["education"]["program"], CV_SOURCE)
require("active program status", PROFILE["education"]["status"], WEBSITE_TEXT)
require("active program status", PROFILE["education"]["status"], CV_SOURCE)
require("active program expected date", PROFILE["education"]["expected"], WEBSITE_TEXT)
require("active program expected date", PROFILE["education"]["expected"], CV_SOURCE)
require("issuer", PROFILE["education"]["issuer"], WEBSITE_TEXT)
require("issuer", PROFILE["education"]["issuer"], CV_SOURCE)

stale_phrases = (
    "4+ years",
    "Five roles",
    "Data Analytics Product Owner, Business Intelligence and Integrations",
    "Technical Software Support Engineer L2, Data & Integrations",
    "Business Development Engineer",
    "Business Development Specialist, Sales & Customer Success",
    "Business Development Specialist, Sales & UX",
    "Jun 2026 - Present",
    "Dec 2025 - Jun 2026",
    "Certified Web Project Manager & Data Analyst",
    "20 LinkedIn-listed",
)

for stale in stale_phrases:
    forbid("website claim", stale, WEBSITE_TEXT)
    forbid("CV claim", stale, CV_SOURCE)

print("Profile claims validated against data/profile.json")
