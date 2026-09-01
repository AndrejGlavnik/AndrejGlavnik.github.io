#!/usr/bin/env python3
"""Build three deterministic, synthetic analytics portfolio projects.

The script intentionally uses only the Python standard library.  It creates the
reviewable CSV sources, executes SQLite analytics queries, writes executed
Jupyter notebooks, authors canonical Data Analytics artifact payloads, and then
packages each payload with the shared portable-artifact builder.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import datetime as dt
import hashlib
import io
import json
import math
import os
import random
import shutil
import sqlite3
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DATE = dt.date(2026, 6, 30)
GENERATED_AT = "2026-06-30T18:00:00Z"
PORTABLE_FAVICON = (
    '<link rel="icon" href="data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%2016%2016%22%3E%3Crect%20width=%2216%22%20height=%2216%22%20rx=%223%22%20fill=%22%230d0d0d%22/%3E%3Ctext%20x=%228%22%20y=%2211.5%22%20text-anchor=%22middle%22%20font-size=%228%22%20fill=%22white%22%3EAG%3C/text%3E%3C/svg%3E" />'
)

DASHBOARD_EVIDENCE = {
    "ga4-quality-monitor": {
        "qa_path": "docs/qa-report.md",
        "qa_label": "QA report",
    },
    "analytics-change-control": {
        "qa_path": "docs/qa-report.md",
        "qa_label": "QA report",
    },
    "marketing-command-center": {
        "qa_path": "docs/methodology.md",
        "qa_label": "Methodology",
    },
}

DASHBOARD_EVIDENCE_STYLE = """
.portfolio-evidence-nav{position:relative;z-index:100;display:flex;align-items:center;gap:16px;width:100%;padding:10px clamp(16px,3vw,32px);border-bottom:1px solid var(--portable-border);background:var(--portable-canvas);font-family:ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.portfolio-evidence-nav>strong{flex:0 0 auto;color:var(--portable-muted);font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}
.portfolio-evidence-links{display:flex;flex-wrap:wrap;gap:6px;min-width:0}
.portfolio-evidence-links a{display:inline-flex;align-items:center;justify-content:center;min-height:34px;padding:6px 10px;border:1px solid var(--portable-border);border-radius:999px;background:var(--portable-surface);color:var(--portable-ink);font-size:12px;font-weight:600;line-height:1.25;text-align:center;text-decoration:none}
.portfolio-evidence-links a:hover,.portfolio-evidence-links a:focus-visible{border-color:var(--portable-accent);color:var(--portable-accent)}
.portfolio-evidence-links a:focus-visible{outline:2px solid var(--portable-accent);outline-offset:2px}
.portfolio-evidence-links .portfolio-return-link{border-color:transparent;background:var(--portable-accent);color:#fff}
.portfolio-evidence-links .portfolio-return-link:hover,.portfolio-evidence-links .portfolio-return-link:focus-visible{border-color:transparent;color:#fff;filter:brightness(.94)}
@media screen and (max-width:760px){.portfolio-evidence-nav{align-items:stretch;flex-direction:column;gap:8px;padding:14px 16px}.portfolio-evidence-links{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}.portfolio-evidence-links a{min-width:0;padding-inline:8px;overflow-wrap:anywhere}}
@media print{.portfolio-evidence-nav{display:none!important}}
""".strip()


def discover_portable_builder():
    """Resolve the canonical builder without embedding a workstation path."""
    relative = Path("skills/build-report/scripts/deliver_portable_artifact.mjs")
    configured = os.environ.get("CODEX_DATA_ANALYTICS_PLUGIN_ROOT")
    candidates = []
    if configured:
        candidates.append(Path(configured).expanduser())
    cache_root = (
        Path.home() / ".codex/plugins/cache/openai-curated-remote/data-analytics"
    )
    if cache_root.is_dir():
        candidates.extend(sorted(cache_root.iterdir(), reverse=True))
    for candidate in candidates:
        builder = candidate / relative
        if builder.is_file():
            return builder
    return None


PORTABLE_BUILDER = discover_portable_builder()


def date_range(start: dt.date, end: dt.date):
    current = start
    while current <= end:
        yield current
        current += dt.timedelta(days=1)


def iso(value):
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    return value


def safe_div(numerator, denominator, default=0.0):
    return numerator / denominator if denominator else default


def median(values):
    values = list(values)
    return statistics.median(values) if values else 0.0


def percentile(values, pct):
    values = sorted(values)
    if not values:
        return 0.0
    position = (len(values) - 1) * pct
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return values[lower]
    return values[lower] + (values[upper] - values[lower]) * (position - lower)


def reset_project(project_dir: Path):
    project_dir.mkdir(parents=True, exist_ok=True)
    for child in list(project_dir.iterdir()):
        if child.name == "index.html" or child.is_file() or child.is_symlink():
            child.unlink()
        elif child.is_dir():
            shutil.rmtree(child)
    for subdir in ("data/raw", "data/curated", "sql", "notebooks", "docs"):
        (project_dir / subdir).mkdir(parents=True, exist_ok=True)


def write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: iso(row.get(key, "")) for key in fieldnames})


def sha256(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_for(project_dir: Path, seed: int, scenario_version: str):
    files = []
    for path in sorted(project_dir.rglob("*")):
        if path.is_file() and path.name not in {"build-manifest.json", "index.html", "portable-build-receipt.json"}:
            files.append(
                {
                    "path": path.relative_to(project_dir).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
    payload = {
        "synthetic": True,
        "scenario_version": scenario_version,
        "seed": seed,
        "snapshot_date": SNAPSHOT_DATE.isoformat(),
        "generated_at": GENERATED_AT,
        "generator": "scripts/build_analytics_projects.py",
        "files": files,
    }
    write_json(project_dir / "data/build-manifest.json", payload)


def execute_notebook(project_dir: Path, cells):
    """Execute simple Python cells in-order and persist a valid nbformat 4 file."""
    namespace = {"__name__": "__main__"}
    execution_count = 0
    rendered = []
    original_cwd = Path.cwd()
    os.chdir(project_dir)
    try:
        for cell_type, source in cells:
            if cell_type == "markdown":
                rendered.append(
                    {
                        "cell_type": "markdown",
                        "metadata": {},
                        "source": source.splitlines(keepends=True),
                    }
                )
                continue
            execution_count += 1
            output = io.StringIO()
            try:
                with contextlib.redirect_stdout(output):
                    exec(compile(source, f"notebook-cell-{execution_count}", "exec"), namespace)
            except Exception as exc:  # fail the build instead of saving a misleading notebook
                raise RuntimeError(
                    f"Notebook cell {execution_count} failed in {project_dir}: {exc}"
                ) from exc
            outputs = []
            if output.getvalue():
                outputs.append(
                    {
                        "name": "stdout",
                        "output_type": "stream",
                        "text": output.getvalue().splitlines(keepends=True),
                    }
                )
            rendered.append(
                {
                    "cell_type": "code",
                    "execution_count": execution_count,
                    "metadata": {},
                    "outputs": outputs,
                    "source": source.splitlines(keepends=True),
                }
            )
    finally:
        os.chdir(original_cwd)
    return {
        "cells": rendered,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": sys.version.split()[0]},
            "portfolio_execution": {
                "executed": True,
                "executed_at": GENERATED_AT,
                "runner": "stdlib deterministic cell runner",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def artifact_source(source_id, label, sql, tables, definitions, source_path, filters):
    return {
        "id": source_id,
        "label": label,
        "path": source_path,
        "query": {
            "engine": "SQLite 3",
            "language": "sql",
            "id": source_id.upper(),
            "description": "Deterministic query executed by scripts/build_analytics_projects.py.",
            "executed_at": GENERATED_AT,
            "tables_used": tables,
            "filters": filters,
            "metric_definitions": definitions,
            "sql": sql,
        },
    }


def add_dashboard_evidence_navigation(project_dir: Path, html: str):
    """Add durable portfolio and source links to a generated dashboard."""
    project_slug = project_dir.name
    config = DASHBOARD_EVIDENCE.get(project_slug)
    if config is None:
        raise KeyError(f"Dashboard evidence configuration missing for {project_slug}")

    github_project = (
        "https://github.com/AndrejGlavnik/AndrejGlavnik.github.io/"
        f"tree/main/projects/{project_slug}"
    )
    github_blob = (
        "https://github.com/AndrejGlavnik/AndrejGlavnik.github.io/"
        f"blob/main/projects/{project_slug}"
    )
    links = [
        ("← Portfolio", "../../#builds", False, "portfolio-return-link"),
        ("Case study / README", f"{github_blob}/README.md", True, ""),
        ("GitHub", github_project, True, ""),
        ("SQL", f"{github_blob}/sql/analytics.sql", True, ""),
        ("Notebook", f"{github_blob}/notebooks/analysis.ipynb", True, ""),
        ("Data dictionary", f"{github_blob}/docs/data-dictionary.md", True, ""),
        (config["qa_label"], f"{github_blob}/{config['qa_path']}", True, ""),
        ("Reproduce", f"{github_blob}/README.md#reproduce", True, ""),
    ]
    anchor_html = []
    for label, href, external, class_name in links:
        class_attribute = f' class="{class_name}"' if class_name else ""
        external_attributes = (
            ' target="_blank" rel="noopener"'
            f' aria-label="{label} (opens in a new tab)"'
            if external else ""
        )
        anchor_html.append(
            f'<a{class_attribute} href="{href}"{external_attributes}>{label}</a>'
        )
    navigation = (
        '<nav class="portfolio-evidence-nav" '
        'aria-label="Project evidence and navigation">'
        '<strong>Project evidence</strong>'
        f'<div class="portfolio-evidence-links">{"".join(anchor_html)}</div>'
        '</nav>'
    )

    style_marker = "</style>"
    body_marker = "<body>"
    if style_marker not in html or body_marker not in html:
        raise RuntimeError(f"Portable HTML injection markers missing: {project_dir}")
    html = html.replace(
        style_marker,
        f"\n{DASHBOARD_EVIDENCE_STYLE}\n{style_marker}",
        1,
    )
    return html.replace(body_marker, f"{body_marker}\n{navigation}", 1)


def build_artifact(project_dir: Path, manifest, datasets, sources):
    payload = {
        "surface": "dashboard",
        "manifest": {**manifest, "sources": sources},
        "snapshot": {
            "version": 1,
            "generatedAt": GENERATED_AT,
            "status": "fixture",
            "datasets": datasets,
        },
        "sources": sources,
    }
    artifact_path = project_dir / "artifact.json"
    write_json(artifact_path, payload)
    if PORTABLE_BUILDER is None:
        raise FileNotFoundError(
            "Canonical portable builder not found. Install the Data Analytics "
            "plugin or set CODEX_DATA_ANALYTICS_PLUGIN_ROOT."
        )
    command = [
        "node",
        str(PORTABLE_BUILDER),
        "--input",
        str(artifact_path),
        "--output",
        str(project_dir / "index.html"),
    ]
    result = None
    attempts = 0
    last_error = None
    max_delivery_attempts = 12
    for attempts in range(1, max_delivery_attempts + 1):
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        if result.returncode == 0:
            break
        try:
            last_error = json.loads(result.stderr.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            last_error = None
        if not last_error or last_error.get("code") != "reader_timeout":
            break
        if attempts < max_delivery_attempts:
            # The canonical headless reader occasionally exits while its
            # loader is still in the documented transient `fallback` state.
            # Retry only that timeout with a short bounded backoff; manifest,
            # provenance, source and calculation failures still fail fast.
            time.sleep(0.25)
    if result is None or result.returncode:
        raise RuntimeError(
            f"Portable artifact build failed for {project_dir.name} after {attempts} attempt(s):\n"
            f"STDOUT:\n{result.stdout if result else ''}\nSTDERR:\n{result.stderr if result else ''}"
        )
    html_path = project_dir / "index.html"
    html = html_path.read_text(encoding="utf-8")
    head_marker = '<meta charset="utf-8" />'
    if PORTABLE_FAVICON not in html:
        if head_marker not in html:
            raise RuntimeError(f"Portable HTML head marker missing: {html_path}")
        html = html.replace(head_marker, f"{head_marker}\n{PORTABLE_FAVICON}", 1)
    html = add_dashboard_evidence_navigation(project_dir, html)
    html_path.write_text(html, encoding="utf-8")
    receipt = json.loads(result.stdout)
    receipt["html"] = html_path.relative_to(ROOT).as_posix()
    receipt["delivery_attempts"] = attempts
    for failure_screenshot in project_dir.glob("index.html.tmp-*.verification-failure.png"):
        failure_screenshot.unlink()
    write_json(project_dir / "data/portable-build-receipt.json", receipt)
    return receipt


def make_card(card_id, dataset, source_id, label, field, fmt="number", description=None):
    return {
        "id": card_id,
        "dataset": dataset,
        "sourceId": source_id,
        "description": description or label,
        "metrics": [{"label": label, "field": field, "format": fmt}],
    }


def make_chart(chart_id, title, chart_type, dataset, source_id, x, y, *,
               subtitle=None, fmt="number", layout="half", color=None,
               size=None, reference_lines=None, x_type=None):
    encodings = {
        "x": {
            "field": x,
            "type": x_type or (
                "temporal" if "month" in x or "week" in x else "nominal"
            ),
        },
        "y": {"field": y, "type": "quantitative", "format": fmt},
    }
    if color:
        encodings["color"] = {"field": color, "type": "nominal"}
    if size:
        encodings["size"] = {"field": size, "type": "quantitative"}
    return {
        "id": chart_id,
        "title": title,
        **({"subtitle": subtitle} if subtitle else {}),
        "type": chart_type,
        "dataset": dataset,
        "sourceId": source_id,
        "encodings": encodings,
        "valueFormat": fmt,
        "layout": layout,
        "referenceLines": reference_lines or [],
        "surface": {"viewMode": "both", "showControls": True},
    }


def load_sqlite_table(connection, table_name, rows, columns):
    column_sql = ", ".join('"{}" {}'.format(name.replace('"', '""'), kind) for name, kind in columns)
    connection.execute(f"CREATE TABLE {table_name} ({column_sql})")
    placeholders = ",".join("?" for _ in columns)
    connection.executemany(
        f"INSERT INTO {table_name} VALUES ({placeholders})",
        [[row[name] for name, _ in columns] for row in rows],
    )


def query_rows(connection, sql):
    cursor = connection.execute(sql)
    fields = [item[0] for item in cursor.description]
    return [dict(zip(fields, row)) for row in cursor.fetchall()]


def build_commercial(project_dir: Path):
    seed = 41001
    rng = random.Random(seed)
    forecast_rng = random.Random(seed + 101)
    reset_project(project_dir)

    markets = ["North", "South", "Central", "West"]
    channels = ["Grocery", "Convenience", "Ecommerce", "Wholesale"]
    products = [
        ("SKU-01", "Aster Sparkling", "Aster", "Hydration", 2.20, 0.76, 34),
        ("SKU-02", "Aster Still", "Aster", "Hydration", 1.80, 0.62, 40),
        ("SKU-03", "Vela Citrus", "Vela", "Hydration", 2.60, 0.93, 28),
        ("SKU-04", "Vela Berry", "Vela", "Hydration", 2.70, 0.97, 26),
        ("SKU-05", "Luma Oats", "Luma", "Breakfast", 3.80, 1.44, 24),
        ("SKU-06", "Luma Granola", "Luma", "Breakfast", 4.60, 1.83, 22),
        ("SKU-07", "Northstar Porridge", "Northstar", "Breakfast", 4.20, 1.62, 20),
        ("SKU-08", "Halo Muesli", "Halo", "Breakfast", 4.90, 1.94, 18),
        ("SKU-09", "Orbit Bar", "Orbit", "Snacks", 1.70, 0.58, 45),
        ("SKU-10", "Orbit Bites", "Orbit", "Snacks", 2.90, 1.02, 31),
        ("SKU-11", "Aster Crunch", "Aster", "Snacks", 3.30, 1.21, 27),
        ("SKU-12", "Vela Mix", "Vela", "Snacks", 3.60, 1.34, 25),
        ("SKU-13", "Luma Oat Drink", "Luma", "Plant-Based", 3.20, 1.28, 23),
        ("SKU-14", "Halo Almond Drink", "Halo", "Plant-Based", 3.70, 1.51, 19),
        ("SKU-15", "Vela Protein Shake", "Vela", "Plant-Based", 4.40, 1.88, 17),
        ("SKU-16", "Orbit Plant Snack", "Orbit", "Plant-Based", 3.10, 1.18, 21),
    ]
    product_lookup = {item[0]: item for item in products}
    market_factor = {"North": 1.18, "South": 1.02, "Central": 1.27, "West": 0.86}
    channel_factor = {"Grocery": 1.25, "Convenience": 0.77, "Ecommerce": 0.72, "Wholesale": 1.08}
    seasonality = {1: 0.87, 2: 0.90, 3: 0.98, 4: 1.03, 5: 1.10, 6: 1.16,
                   7: 1.20, 8: 1.15, 9: 1.03, 10: 0.98, 11: 1.07, 12: 1.19}

    promotions = []
    promo_lookup = {}
    promo_number = 0
    mechanics = ["Feature", "Display", "Bundle", "Price cut"]
    execution_lift = {
        "Feature": 0.25,
        "Display": 0.35,
        "Bundle": 0.22,
        "Price cut": 0.08,
    }
    for year, month in [(2025, month) for month in range(1, 13)] + [(2026, month) for month in range(1, 7)]:
        selected = rng.sample(
            [(product[0], market, channel) for product in products for market in markets for channel in channels],
            8,
        )
        for index, (sku_id, market, channel) in enumerate(selected):
            promo_number += 1
            start_day = 2 + index * 3
            start = dt.date(year, month, min(start_day, 24))
            end = min(start + dt.timedelta(days=8 + index % 5),
                      (dt.date(year + (month == 12), month % 12 + 1, 1) - dt.timedelta(days=1)))
            discounts = [0.10, 0.15, 0.20, 0.30]
            discount = (
                0.30
                if market == "South" and year == 2026 and month >= 4 and index < 4
                else discounts[(promo_number - 1) % len(discounts)]
            )
            mechanic = mechanics[(index + month) % len(mechanics)]
            promo = {
                "promo_id": f"PROMO-{promo_number:03d}",
                "sku_id": sku_id,
                "market": market,
                "channel": channel,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "mechanic": mechanic,
                "discount_pct": discount,
                "execution_lift_pct": execution_lift[mechanic],
                "activation_cost_eur": round(25 + rng.random() * 100, 2),
            }
            promotions.append(promo)
            for day in date_range(start, end):
                promo_lookup[(day.isoformat(), sku_id, market, channel)] = promo

    sales = []
    budget_agg = defaultdict(lambda: {
        "budget_units": 0,
        "budget_revenue_eur": 0.0,
        "forecast_basis_units": 0,
        "forecast_units": 0,
        "forecast_revenue_eur": 0.0,
    })
    promo_agg = defaultdict(lambda: {"actual_units": 0, "baseline_units": 0,
                                     "actual_contribution": 0.0, "baseline_contribution": 0.0,
                                     "discount_value": 0.0})
    start_date = dt.date(2025, 1, 1)
    for date in date_range(start_date, SNAPSHOT_DATE):
        day_index = (date - start_date).days
        weekday_factor = 1.10 if date.weekday() in (4, 5) else (0.92 if date.weekday() == 0 else 1.0)
        trend = 1 + day_index * 0.00011
        for sku_id, product_name, brand, category, list_price, unit_cost, base_demand in products:
            category_season = 1.11 if category == "Hydration" and date.month in (5, 6, 7, 8) else 1.0
            for market in markets:
                for channel in channels:
                    planning_baseline_float = (
                        base_demand * market_factor[market] * channel_factor[channel]
                        * weekday_factor * seasonality[date.month] * trend
                        * category_season
                    )
                    baseline_float = planning_baseline_float * rng.uniform(0.86, 1.14)
                    if sku_id == "SKU-07" and date.year == 2026 and date.month == 5:
                        baseline_float *= 0.56
                    planning_units = max(1, round(planning_baseline_float))
                    baseline_units = max(1, round(baseline_float))
                    promo = promo_lookup.get((date.isoformat(), sku_id, market, channel))
                    discount = promo["discount_pct"] if promo else 0.0
                    elasticity = {"Hydration": 2.7, "Breakfast": 2.2, "Snacks": 3.1, "Plant-Based": 2.0}[category]
                    uplift = 1 + elasticity * discount
                    if promo:
                        uplift += promo["execution_lift_pct"]
                    if discount >= 0.30:
                        uplift *= 0.78
                    forecast_basis_units = max(1, round(planning_units * uplift))
                    gross_units = max(1, round(baseline_units * uplift))
                    return_rate = 0.042 if channel == "Ecommerce" else (0.014 if channel == "Convenience" else 0.008)
                    return_units = min(gross_units, round(gross_units * return_rate * rng.uniform(0.7, 1.3)))
                    net_units = gross_units - return_units
                    price_factor = {"North": 1.05, "South": 0.94, "Central": 1.00, "West": 0.97}[market]
                    realized_list_price = list_price * price_factor
                    gross_revenue = gross_units * realized_list_price
                    return_value = return_units * realized_list_price
                    discount_value = net_units * realized_list_price * discount
                    net_revenue = gross_revenue - return_value - discount_value
                    cost = unit_cost * (1 + max(0, day_index) / 365 * 0.018)
                    cogs = net_units * cost
                    gross_profit = net_revenue - cogs
                    month_key = date.strftime("%Y-%m")
                    budget_units = max(1, round(planning_units * 1.04))
                    budget_revenue = budget_units * realized_list_price * 0.96
                    forecast_units = max(
                        1,
                        round(forecast_basis_units * forecast_rng.uniform(0.92, 1.08)),
                    )
                    forecast_revenue = forecast_units * realized_list_price * 0.96
                    budget_key = (month_key, sku_id, market, channel)
                    budget_agg[budget_key]["budget_units"] += budget_units
                    budget_agg[budget_key]["budget_revenue_eur"] += budget_revenue
                    budget_agg[budget_key]["forecast_basis_units"] += forecast_basis_units
                    budget_agg[budget_key]["forecast_units"] += forecast_units
                    budget_agg[budget_key]["forecast_revenue_eur"] += forecast_revenue
                    row = {
                        "date": date.isoformat(), "month": month_key, "sku_id": sku_id,
                        "product_name": product_name, "brand": brand, "category": category,
                        "market": market, "channel": channel, "promo_id": promo["promo_id"] if promo else "",
                        "gross_units": gross_units, "return_units": return_units, "net_units": net_units,
                        "baseline_units": baseline_units, "list_price_eur": round(realized_list_price, 4),
                        "discount_pct": discount, "gross_revenue_eur": round(gross_revenue, 2),
                        "return_value_eur": round(return_value, 2), "discount_value_eur": round(discount_value, 2),
                        "net_revenue_eur": round(net_revenue, 2), "cogs_eur": round(cogs, 2),
                        "gross_profit_eur": round(gross_profit, 2),
                    }
                    sales.append(row)
                    if promo:
                        aggregate = promo_agg[promo["promo_id"]]
                        aggregate["actual_units"] += net_units
                        aggregate["baseline_units"] += baseline_units
                        aggregate["actual_contribution"] += gross_profit
                        aggregate["baseline_contribution"] += baseline_units * (realized_list_price - cost)
                        aggregate["discount_value"] += discount_value

    budgets = []
    for (month_key, sku_id, market, channel), values in sorted(budget_agg.items()):
        month_start = dt.date.fromisoformat(f"{month_key}-01")
        budgets.append({
            "month": month_key, "sku_id": sku_id, "market": market, "channel": channel,
            "forecast_locked_at": (month_start - dt.timedelta(days=1)).isoformat(),
            "forecast_method": "calendar_plan_v1_no_realized_demand",
            "budget_units": values["budget_units"],
            "budget_revenue_eur": round(values["budget_revenue_eur"], 2),
            "forecast_basis_units": values["forecast_basis_units"],
            "forecast_units": values["forecast_units"],
            "forecast_revenue_eur": round(values["forecast_revenue_eur"], 2),
        })
    for promotion in promotions:
        values = promo_agg[promotion["promo_id"]]
        activation = promotion["activation_cost_eur"]
        incremental_profit = values["actual_contribution"] - values["baseline_contribution"] - activation
        investment = values["discount_value"] + activation
        incremental_profit = round(incremental_profit, 2)
        investment = round(investment, 2)
        promotion.update({
            "actual_units": values["actual_units"],
            "baseline_units": values["baseline_units"],
            "unit_uplift_pct": round(safe_div(values["actual_units"] - values["baseline_units"], values["baseline_units"]), 6),
            "discount_value_eur": round(values["discount_value"], 2),
            "incremental_profit_eur": incremental_profit,
            "promotion_investment_eur": investment,
            "promotion_roi": round(safe_div(incremental_profit, investment), 6),
        })

    write_csv(project_dir / "data/raw/sales_daily.csv", list(sales[0]), sales)
    write_csv(project_dir / "data/raw/budget_forecast.csv", list(budgets[0]), budgets)
    write_csv(project_dir / "data/raw/promotions.csv", list(promotions[0]), promotions)

    con = sqlite3.connect(":memory:")
    load_sqlite_table(con, "fact_sales", sales, [
        ("date", "TEXT"), ("month", "TEXT"), ("sku_id", "TEXT"), ("product_name", "TEXT"),
        ("brand", "TEXT"), ("category", "TEXT"), ("market", "TEXT"), ("channel", "TEXT"),
        ("promo_id", "TEXT"), ("gross_units", "INTEGER"), ("return_units", "INTEGER"),
        ("net_units", "INTEGER"), ("baseline_units", "INTEGER"), ("list_price_eur", "REAL"),
        ("discount_pct", "REAL"), ("gross_revenue_eur", "REAL"), ("return_value_eur", "REAL"),
        ("discount_value_eur", "REAL"), ("net_revenue_eur", "REAL"), ("cogs_eur", "REAL"),
        ("gross_profit_eur", "REAL"),
    ])
    load_sqlite_table(con, "fact_budget_forecast", budgets, [
        ("month", "TEXT"), ("sku_id", "TEXT"), ("market", "TEXT"), ("channel", "TEXT"),
        ("forecast_locked_at", "TEXT"), ("forecast_method", "TEXT"),
        ("budget_units", "INTEGER"), ("budget_revenue_eur", "REAL"),
        ("forecast_basis_units", "INTEGER"),
        ("forecast_units", "INTEGER"), ("forecast_revenue_eur", "REAL"),
    ])
    load_sqlite_table(con, "fact_promotion", promotions, [
        ("promo_id", "TEXT"), ("sku_id", "TEXT"), ("market", "TEXT"), ("channel", "TEXT"),
        ("start_date", "TEXT"), ("end_date", "TEXT"), ("mechanic", "TEXT"),
        ("discount_pct", "REAL"), ("execution_lift_pct", "REAL"),
        ("activation_cost_eur", "REAL"), ("actual_units", "INTEGER"),
        ("baseline_units", "INTEGER"), ("unit_uplift_pct", "REAL"), ("discount_value_eur", "REAL"),
        ("incremental_profit_eur", "REAL"), ("promotion_investment_eur", "REAL"),
        ("promotion_roi", "REAL"),
    ])

    sql_summary = """
WITH actual_by_slice AS (
  SELECT month, sku_id, market, channel,
         SUM(net_units) AS actual_units,
         SUM(net_revenue_eur) AS net_revenue,
         SUM(gross_profit_eur) AS gross_profit
  FROM fact_sales GROUP BY month, sku_id, market, channel
), actual AS (
  SELECT SUM(net_revenue) AS net_revenue,
         SUM(gross_profit) AS gross_profit,
         SUM(actual_units) AS net_units,
         SUM(ABS(actual_units - forecast_units)) AS absolute_forecast_error,
         SUM(actual_units) AS actual_units
  FROM actual_by_slice
  JOIN fact_budget_forecast USING (month, sku_id, market, channel)
), plan AS (
  SELECT SUM(budget_revenue_eur) AS budget_revenue FROM fact_budget_forecast
)
SELECT ROUND(net_revenue, 2) AS net_revenue,
       ROUND((net_revenue - budget_revenue) / budget_revenue, 6) AS budget_variance_rate,
       ROUND(gross_profit / net_revenue, 6) AS gross_margin_rate,
       net_units,
       ROUND(absolute_forecast_error * 1.0 / actual_units, 6) AS forecast_wape
FROM actual CROSS JOIN plan;
""".strip()
    sql_monthly = """
SELECT s.month,
       ROUND(SUM(s.net_revenue_eur), 2) AS actual_revenue,
       ROUND(MAX(b.budget_revenue), 2) AS budget_revenue,
       ROUND(SUM(s.gross_profit_eur), 2) AS gross_profit
FROM fact_sales s
JOIN (SELECT month, SUM(budget_revenue_eur) AS budget_revenue
      FROM fact_budget_forecast GROUP BY month) b ON b.month = s.month
GROUP BY s.month ORDER BY s.month;
""".strip()
    sql_market = """
WITH budgets AS (
  SELECT market, SUM(budget_revenue_eur) AS budget_revenue
  FROM fact_budget_forecast GROUP BY market
)
SELECT s.market,
       ROUND(SUM(s.net_revenue_eur), 2) AS net_revenue,
       ROUND(SUM(s.gross_profit_eur) / SUM(s.net_revenue_eur), 6) AS gross_margin_rate,
       ROUND((SUM(s.net_revenue_eur) - MAX(b.budget_revenue)) / MAX(b.budget_revenue), 6) AS budget_variance_rate
FROM fact_sales s JOIN budgets b ON b.market = s.market
GROUP BY s.market ORDER BY net_revenue DESC;
""".strip()
    sql_promo = """
SELECT CASE
         WHEN discount_pct < .125 THEN '10%'
         WHEN discount_pct < .175 THEN '15%'
         WHEN discount_pct < .25 THEN '20%'
         ELSE '30%'
       END AS discount_band,
       ROUND(AVG(discount_pct), 4) AS discount_pct,
       ROUND(SUM(incremental_profit_eur), 2) AS incremental_profit_eur,
       ROUND(SUM(promotion_investment_eur), 2) AS promotion_investment_eur,
       ROUND(SUM(incremental_profit_eur) / SUM(promotion_investment_eur), 6) AS promotion_roi,
       ROUND(SUM(actual_units - baseline_units) * 1.0 / SUM(baseline_units), 6) AS unit_uplift_pct
FROM fact_promotion GROUP BY discount_band ORDER BY discount_pct;
""".strip()
    sql_product = """
WITH budgets AS (
  SELECT sku_id, SUM(budget_revenue_eur) AS budget_revenue
  FROM fact_budget_forecast GROUP BY sku_id
)
SELECT s.sku_id, MAX(s.product_name) AS product_name, MAX(s.category) AS category,
       ROUND(SUM(s.net_revenue_eur), 2) AS net_revenue,
       ROUND(SUM(s.gross_profit_eur) / SUM(s.net_revenue_eur), 6) AS gross_margin_rate,
       ROUND((SUM(s.net_revenue_eur) - MAX(b.budget_revenue)) / MAX(b.budget_revenue), 6) AS budget_variance_rate,
       SUM(s.net_units) AS net_units
FROM fact_sales s JOIN budgets b ON b.sku_id = s.sku_id
GROUP BY s.sku_id ORDER BY net_revenue DESC;
""".strip()
    summary = query_rows(con, sql_summary)
    monthly = query_rows(con, sql_monthly)
    market_performance = query_rows(con, sql_market)
    promo_performance = query_rows(con, sql_promo)
    product_performance = query_rows(con, sql_product)
    con.close()

    total = summary[0]
    sales_grain = [
        (row["date"], row["sku_id"], row["market"], row["channel"])
        for row in sales
    ]
    budget_grain = {
        (row["month"], row["sku_id"], row["market"], row["channel"])
        for row in budgets
    }
    actual_grain = {
        (row["month"], row["sku_id"], row["market"], row["channel"])
        for row in sales
    }
    return_violations = sum(
        row["return_units"] > row["gross_units"]
        or row["net_units"] != row["gross_units"] - row["return_units"]
        for row in sales
    )
    revenue_violations = sum(
        abs(
            row["net_revenue_eur"]
            - (
                row["gross_revenue_eur"]
                - row["return_value_eur"]
                - row["discount_value_eur"]
            )
        )
        > 0.011
        for row in sales
    )
    invalid_promotion_windows = sum(
        row["start_date"] > row["end_date"] for row in promotions
    )
    invalid_forecast_locks = sum(
        row["forecast_locked_at"] >= f"{row['month']}-01" for row in budgets
    )
    check_specs = [
        (
            "Daily sales grain is unique",
            len(sales_grain) == len(set(sales_grain)),
            f"{len(sales_grain):,} rows; {len(sales_grain) - len(set(sales_grain))} duplicates",
        ),
        (
            "Returns never exceed gross units",
            return_violations == 0,
            f"{return_violations} violations",
        ),
        (
            "Net revenue formula reconciles",
            revenue_violations == 0,
            f"{revenue_violations} rows outside €0.01 tolerance",
        ),
        (
            "Every sales slice has one budget and locked forecast",
            budget_grain == actual_grain and len(budget_grain) == len(budgets),
            f"{len(budget_grain):,} matched slices",
        ),
        (
            "Forecast is locked before each reporting month",
            invalid_forecast_locks == 0,
            f"{invalid_forecast_locks} invalid lock dates",
        ),
        (
            "Promotion dates are valid",
            invalid_promotion_windows == 0,
            f"{invalid_promotion_windows} invalid windows",
        ),
        (
            "All four planned discount bands are represented",
            {row["discount_pct"] for row in promotions}
            == {0.10, 0.15, 0.20, 0.30},
            f"{len({row['discount_pct'] for row in promotions})} bands",
        ),
        (
            "Discount depth is not confounded with one execution mechanic",
            all(
                len({row["mechanic"] for row in promotions if row["discount_pct"] == band})
                == len(mechanics)
                for band in {0.10, 0.15, 0.20, 0.30}
            ),
            "4 mechanics represented in every discount band",
        ),
        (
            "Dashboard and SQL totals agree",
            abs(sum(row["net_revenue_eur"] for row in sales) - total["net_revenue"])
            <= 0.011,
            "Exact to €0.01",
        ),
    ]
    quality_checks = [
        {
            "check": label,
            "status": "PASS" if passed else "FAIL",
            "result": evidence,
        }
        for label, passed, evidence in check_specs
    ]
    sql_quality = 'SELECT "check" AS "check", status, result FROM quality_checks ORDER BY "check";'
    quality_connection = sqlite3.connect(":memory:")
    load_sqlite_table(quality_connection, "quality_checks", quality_checks, [
        ("check", "TEXT"), ("status", "TEXT"), ("result", "TEXT"),
    ])
    quality_checks = query_rows(quality_connection, sql_quality)
    quality_connection.close()
    write_csv(project_dir / "data/curated/monthly_performance.csv", list(monthly[0]), monthly)
    write_csv(project_dir / "data/curated/market_performance.csv", list(market_performance[0]), market_performance)
    write_csv(project_dir / "data/curated/promotion_performance.csv", list(promo_performance[0]), promo_performance)
    write_csv(project_dir / "data/curated/product_performance.csv", list(product_performance[0]), product_performance)
    write_csv(project_dir / "data/curated/quality_checks.csv", list(quality_checks[0]), quality_checks)
    write_json(project_dir / "data/curated/summary.json", summary[0])

    sql_all = "\n\n-- DASHBOARD: executive summary\n" + sql_summary + \
              "\n\n-- DASHBOARD: monthly trend\n" + sql_monthly + \
              "\n\n-- DASHBOARD: market performance\n" + sql_market + \
              "\n\n-- DASHBOARD: promotion effectiveness\n" + sql_promo + \
              "\n\n-- DASHBOARD: product detail\n" + sql_product + \
              "\n\n-- DASHBOARD: executed quality checks\n" + sql_quality
    write_text(project_dir / "sql/analytics.sql", sql_all)
    write_text(project_dir / "sql/tests.sql", """
-- Every assertion should return zero rows.
SELECT date, sku_id, market, channel, COUNT(*) AS rows_at_grain
FROM fact_sales GROUP BY 1,2,3,4 HAVING COUNT(*) <> 1;

SELECT * FROM fact_sales WHERE return_units > gross_units OR net_units <> gross_units - return_units;

SELECT * FROM fact_sales
WHERE ABS(net_revenue_eur - (gross_revenue_eur - return_value_eur - discount_value_eur)) > 0.011;

SELECT month, sku_id, market, channel, COUNT(*) AS rows_at_grain
FROM fact_budget_forecast GROUP BY 1,2,3,4 HAVING COUNT(*) <> 1;

SELECT * FROM fact_budget_forecast
WHERE forecast_locked_at >= month || '-01'
   OR forecast_method <> 'calendar_plan_v1_no_realized_demand';

SELECT discount_pct, COUNT(DISTINCT mechanic) AS represented_mechanics
FROM fact_promotion
GROUP BY discount_pct
HAVING COUNT(DISTINCT mechanic) <> 4;
""")

    best_promo = max(promo_performance, key=lambda row: row["promotion_roi"])
    weak_market = min(market_performance, key=lambda row: row["budget_variance_rate"])
    profitable_bands = [
        row for row in promo_performance if row["promotion_roi"] > 0
    ]
    if profitable_bands:
        promotion_decision = (
            f"Run a bounded next-quarter test in the {best_promo['discount_band']} "
            f"band (modeled weighted ROI {best_promo['promotion_roi']:.1%}); keep "
            "the modeled baseline and margin guardrail visible before scaling."
        )
    else:
        promotion_decision = (
            "Do not reallocate incremental promotion budget yet: every modeled "
            "band is value-destructive. Rework activation cost or offer economics "
            "before the next test."
        )
    notebook = execute_notebook(project_dir, [
        ("markdown", f"""# Commercial Performance & Promotion Intelligence\n\n## tl;dr\n\nSynthetic net revenue is **€{total['net_revenue']:,.0f}**, gross margin is **{total['gross_margin_rate']:.1%}**, and forecast WAPE is **{total['forecast_wape']:.1%}**. The strongest promotion band by weighted scenario ROI is **{best_promo['discount_band']}**. **{weak_market['market']}** has the weakest budget variance and is the first review segment.\n"""),
        ("markdown", """## Context & Methods\n\nDecision: where should a fictional commercial team reallocate promotion investment while protecting margin? Data is synthetic and generated with seed 41001. Promotion ROI uses a model-derived baseline and is not a causal estimate.\n\n### Key Assumptions\n\n- EUR is the reporting currency.\n- Returns reduce units and revenue.\n- The locked forecast uses calendar, product, market, channel, seasonality and known promotion inputs; it is generated before the month and excludes realized daily demand noise.\n- Promotion scenarios combine category price response with a disclosed mechanic-specific execution lift; every discount band spans all four mechanics.\n"""),
        ("code", """from pathlib import Path\nimport csv, json\nPROJECT_DIR = Path.cwd()\ndef read_csv(name):\n    with (PROJECT_DIR / name).open(encoding='utf-8') as handle:\n        return list(csv.DictReader(handle))\nsummary = json.loads((PROJECT_DIR / 'data/curated/summary.json').read_text())\nmonthly = read_csv('data/curated/monthly_performance.csv')\npromos = read_csv('data/curated/promotion_performance.csv')\nprint(f\"Snapshot: 2026-06-30 | months={len(monthly)} | promotion bands={len(promos)}\")\nprint(json.dumps(summary, indent=2))\n"""),
        ("markdown", """## Data\n\nThe modeled grain is one row per date × SKU × market × channel. Curated files contain only reviewed aggregates used by the dashboard.\n"""),
        ("code", """from collections import Counter\nwith (PROJECT_DIR / 'data/raw/sales_daily.csv').open(encoding='utf-8') as handle:\n    reader = csv.DictReader(handle)\n    row_count = 0\n    categories = Counter()\n    revenue = 0.0\n    gross_profit = 0.0\n    for row in reader:\n        row_count += 1\n        categories[row['category']] += 1\n        revenue += float(row['net_revenue_eur'])\n        gross_profit += float(row['gross_profit_eur'])\nprint(f\"rows={row_count:,} | categories={dict(categories)}\")\nprint(f\"recomputed revenue=€{revenue:,.2f} | margin={gross_profit/revenue:.2%}\")\n"""),
        ("markdown", """## Results\n\nPromotion bands are compared with weighted totals so small promotions do not receive the same influence as large investments.\n"""),
        ("code", """ranked = sorted(promos, key=lambda row: float(row['promotion_roi']), reverse=True)\nfor row in ranked:\n    print(f\"{row['discount_band']:>3} | ROI {float(row['promotion_roi']):>7.1%} | uplift {float(row['unit_uplift_pct']):>7.1%} | investment €{float(row['promotion_investment_eur']):,.0f}\")\n"""),
        ("markdown", f"""## Takeaways\n\n1. **Promotion decision:** {promotion_decision}\n2. Review **{weak_market['market']}** first because its synthetic budget variance is the weakest, not because it has the smallest revenue.\n3. Use the product table to distinguish price/discount pressure from a genuine volume shortfall.\n"""),
    ])
    write_json(project_dir / "notebooks/analysis.ipynb", notebook)

    definitions = [
        "Net Revenue = gross revenue - return value - discount value.",
        "Gross Margin = SUM(gross profit) / SUM(net revenue).",
        "Budget Variance = (actual net revenue - budget net revenue) / budget net revenue.",
        "Forecast WAPE = SUM(ABS(actual units - locked forecast units)) / SUM(actual units); the forecast is locked before each month from ex-ante planning inputs and excludes realized daily noise.",
        "Promotion ROI = incremental profit / (discount value + activation cost); baseline is modeled and scenario uplift combines category elasticity with mechanic-specific execution lift.",
    ]
    commercial_sources = []
    for source_id, label, sql, tables in [
        (
            "commercial_summary",
            "Commercial KPI summary",
            sql_summary,
            ["fact_sales", "fact_budget_forecast"],
        ),
        (
            "commercial_monthly",
            "Monthly revenue and budget",
            sql_monthly,
            ["fact_sales", "fact_budget_forecast"],
        ),
        (
            "commercial_market",
            "Market performance",
            sql_market,
            ["fact_sales", "fact_budget_forecast"],
        ),
        (
            "commercial_promo",
            "Promotion effectiveness",
            sql_promo,
            ["fact_promotion"],
        ),
        (
            "commercial_product",
            "Product decision detail",
            sql_product,
            ["fact_sales", "fact_budget_forecast"],
        ),
    ]:
        commercial_sources.append(artifact_source(
            source_id, label, sql, tables, definitions,
            "sql/analytics.sql", ["2025-01-01 through 2026-06-30", "Synthetic company and entities"],
        ))
    commercial_sources.append(artifact_source(
        "commercial_quality", "Executed commercial QA checks", sql_quality,
        ["quality_checks"], definitions, "sql/analytics.sql",
        ["Independent deterministic build checks"],
    ))
    cards = [
        make_card("net_revenue", "summary", "commercial_summary", "Net revenue", "net_revenue", "currency", "Revenue after returns and discounts."),
        make_card("budget_variance", "summary", "commercial_summary", "Vs budget", "budget_variance_rate", "percent", "Actual net revenue versus the complete-period budget."),
        make_card("gross_margin", "summary", "commercial_summary", "Gross margin", "gross_margin_rate", "percent", "Weighted gross profit divided by net revenue."),
        make_card("net_units", "summary", "commercial_summary", "Net units", "net_units", "compact", "Gross units less returned units."),
        make_card("forecast_wape", "summary", "commercial_summary", "Forecast WAPE", "forecast_wape", "percent", "Absolute locked-forecast unit error divided by actual units; lower is better."),
    ]
    charts = [
        {
            **make_chart("monthly_revenue", "Net revenue and budget by month", "line", "monthly", "commercial_monthly", "month", "actual_revenue", subtitle="Complete months · EUR · Jan 2025–Jun 2026", fmt="currency", layout="full"),
            "encodings": {
                "x": {"field": "month", "type": "temporal"},
                "y": {"fields": ["actual_revenue", "budget_revenue"], "type": "quantitative", "format": "currency"},
            },
        },
        make_chart(
            "promo_roi",
            "Weighted modeled ROI by discount band",
            "horizontalBar",
            "promo_performance",
            "commercial_promo",
            "discount_band",
            "promotion_roi",
            subtitle="Four planned bands; ratio of summed incremental profit to summed investment",
            fmt="percent",
            layout="full",
        ),
        make_chart("product_revenue", "Net revenue by product", "leaderboard", "product_performance", "commercial_product", "product_name", "net_revenue", subtitle="Click table view for margin and budget context", fmt="currency", layout="full"),
    ]
    tables = [
        {
            "id": "market_table", "title": "Market performance", "subtitle": "Revenue, weighted margin and budget variance",
            "dataset": "market_performance", "sourceId": "commercial_market", "layout": "full",
            "density": "dense", "defaultSort": {"field": "net_revenue", "direction": "desc"},
            "columns": [
                {"field": "market", "label": "Market", "type": "text"},
                {"field": "net_revenue", "label": "Net revenue", "format": "currency"},
                {"field": "gross_margin_rate", "label": "Gross margin", "format": "percent"},
                {"field": "budget_variance_rate", "label": "Vs budget", "format": "percent", "movement": True},
            ],
        },
        {
            "id": "promo_table", "title": "Promotion decision detail",
            "subtitle": "Modeled scenario evidence; not a causal experiment",
            "dataset": "promo_performance", "sourceId": "commercial_promo", "layout": "full",
            "density": "dense", "defaultSort": {"field": "promotion_roi", "direction": "desc"},
            "columns": [
                {"field": "discount_band", "label": "Discount band", "type": "text"},
                {"field": "promotion_roi", "label": "Weighted ROI", "format": "percent"},
                {"field": "unit_uplift_pct", "label": "Modeled unit uplift", "format": "percent"},
                {"field": "incremental_profit_eur", "label": "Incremental profit", "format": "currency"},
                {"field": "promotion_investment_eur", "label": "Investment", "format": "currency"},
            ],
        },
        {
            "id": "product_table", "title": "Product decision detail",
            "subtitle": "Revenue, margin, budget variance and units",
            "dataset": "product_performance", "sourceId": "commercial_product", "layout": "full",
            "density": "dense", "defaultSort": {"field": "net_revenue", "direction": "desc"},
            "columns": [
                {"field": "product_name", "label": "Product", "type": "text"},
                {"field": "category", "label": "Category", "type": "text"},
                {"field": "net_revenue", "label": "Net revenue", "format": "currency"},
                {"field": "gross_margin_rate", "label": "Gross margin", "format": "percent"},
                {"field": "budget_variance_rate", "label": "Vs budget", "format": "percent", "movement": True},
                {"field": "net_units", "label": "Net units", "format": "compact"},
            ],
        },
        {
            "id": "quality_table", "title": "Quality and reconciliation evidence",
            "dataset": "quality_checks", "sourceId": "commercial_quality", "layout": "full",
            "density": "dense", "defaultSort": {"field": "check", "direction": "asc"},
            "columns": [
                {"field": "check", "label": "Check", "type": "text"},
                {"field": "status", "label": "Status", "type": "text"},
                {"field": "result", "label": "Evidence", "type": "text"},
            ],
        },
    ]
    blocks = [
        {"id": "intro", "type": "markdown", "body": "# Commercial Performance & Promotion Intelligence\n\n**Decision:** where should a fictional commercial team reallocate next-quarter promotion investment while protecting net revenue and gross margin?\n\n*Deterministic synthetic portfolio data · snapshot 30 Jun 2026 · no employer or customer information.*"},
        {"id": "metrics", "type": "metric-strip", "cardIds": [card["id"] for card in cards]},
        {"id": "trend", "type": "chart", "chartId": "monthly_revenue", "layout": "full"},
        {"id": "market", "type": "table", "tableId": "market_table", "layout": "full"},
        {
            "id": "promotion_decision",
            "type": "markdown",
            "sourceId": "commercial_promo",
            "body": f"## Promotion decision\n\n**Recommendation:** {promotion_decision}",
        },
        {"id": "promo", "type": "chart", "chartId": "promo_roi", "layout": "full"},
        {"id": "promo_detail", "type": "table", "tableId": "promo_table", "layout": "full"},
        {"id": "product_chart", "type": "chart", "chartId": "product_revenue", "layout": "full"},
        {"id": "product_detail", "type": "table", "tableId": "product_table", "layout": "full"},
        {"id": "quality", "type": "table", "tableId": "quality_table", "layout": "full"},
        {"id": "limitations", "type": "markdown", "body": "## Method and limitations\n\nPromotion baselines are modeled, so ROI is scenario analysis rather than a causal experiment. Budget and actual cover the same complete period. Exact formulas, SQL, data dictionary, notebook and QA evidence are included beside this dashboard."},
    ]
    artifact_manifest = {
        "version": 1, "surface": "dashboard",
        "title": "Commercial Performance & Promotion Intelligence",
        "description": "A decision-focused synthetic FMCG commercial analytics dashboard.",
        "generatedAt": GENERATED_AT, "cards": cards, "charts": charts,
        "tables": tables, "blocks": blocks,
    }
    datasets = {
        "summary": summary, "monthly": monthly, "market_performance": market_performance,
        "promo_performance": promo_performance, "product_performance": product_performance,
        "quality_checks": quality_checks,
    }
    write_json(project_dir / "data/curated/dashboard-data.json", datasets)
    write_text(project_dir / "README.md", f"""
# Commercial Performance & Promotion Intelligence

Decision-focused BI/Data Analyst portfolio project using deterministic synthetic data.

## Decision

Where should a fictional commercial team reallocate next-quarter promotional investment to protect net revenue and improve gross margin without avoidable volume loss?

## Reproduce

From the repository root:

```bash
python3 scripts/build_analytics_projects.py --project commercial
python3 scripts/validate_portfolio_data.py --project commercial
```

## Evidence

- Raw grain: one row per date × SKU × market × channel
- Rows: {len(sales):,}
- Period: 1 Jan 2025–30 Jun 2026
- Seed: {seed}
- Executed SQL: `sql/analytics.sql`
- Executed notebook: `notebooks/analysis.ipynb`
- Canonical portable artifact: `artifact.json` → `index.html`

All companies, products, values and outcomes are fictional. Promotion ROI uses a modeled baseline and must not be interpreted as a causal estimate.
""")
    write_text(project_dir / "docs/metric-dictionary.md", "# Metric dictionary\n\n" + "\n".join(f"- {item}" for item in definitions))
    write_text(project_dir / "docs/data-dictionary.md", """
# Data dictionary

## fact_sales

One row per date × SKU × market × channel. Revenue is expressed in EUR. `baseline_units` is a model-generated no-promotion planning baseline.

## fact_budget_forecast

One row per month × SKU × market × channel containing budget, ex-ante forecast basis, lock date and locked unit/revenue forecast. Forecast inputs exclude realized daily demand noise.

## fact_promotion

One row per promotion with date window, discount, execution mechanic, disclosed mechanic-specific lift assumption, activation cost, modeled uplift and derived scenario ROI. Each discount band spans all four mechanics so discount depth is not a proxy for one execution type.
""")
    write_text(project_dir / "docs/methodology.md", """
# Methodology and limitations

The generator combines fixed product economics, channel and market factors, weekday and seasonal effects, a bounded deterministic actual-demand noise term and explicit promotion/supply scenarios. Promotion uplift combines category price elasticity with a disclosed mechanic-specific execution lift (Feature 25%, Display 35%, Bundle 22%, Price cut 8%); a saturation factor is applied at 30% discount. Every discount band spans all four mechanics. The locked forecast is generated independently from ex-ante calendar and planning inputs before each month, so realized daily noise cannot leak into forecast accuracy. The exact magnitudes are calculated after generation; no headline KPI is manually typed into the dashboard.

Promotion ROI compares actual scenario contribution with a modeled, model-derived no-promotion baseline. The response and execution assumptions are fictional scenario inputs, not fitted estimates; the result is useful for demonstrating analytical method, not for making causal claims about a real promotion.
""")
    write_text(project_dir / "docs/qa-report.md", "# QA report\n\n" + "\n".join(f"- **{row['status']}** — {row['check']}: {row['result']}" for row in quality_checks))
    receipt = build_artifact(project_dir, artifact_manifest, datasets, commercial_sources)
    manifest_for(project_dir, seed, "commercial-v1")
    return {"project": "commercial", "rows": len(sales), "receipt": receipt, "summary": total}


def build_reliability(project_dir: Path):
    seed = 42002
    rng = random.Random(seed)
    reset_project(project_dir)
    assets = [
        {"asset_id": "WEB_EVENTS", "asset_name": "Web events", "source_system": "Web SDK", "criticality": "Critical", "owner": "Web Analytics", "freshness_sla_minutes": 240},
        {"asset_id": "CRM_LEADS", "asset_name": "CRM leads", "source_system": "CRM API", "criticality": "Critical", "owner": "Revenue Analytics", "freshness_sla_minutes": 240},
        {"asset_id": "COMMERCE_ORDERS", "asset_name": "Commerce orders", "source_system": "Commerce API", "criticality": "Critical", "owner": "Analytics Engineering", "freshness_sla_minutes": 240},
        {"asset_id": "CAMPAIGN_SPEND", "asset_name": "Campaign spend", "source_system": "Media connectors", "criticality": "High", "owner": "Marketing Operations", "freshness_sla_minutes": 240},
    ]
    rules = [
        {"rule_id": "DQ-UNIQUE", "rule_name": "Business key uniqueness", "dimension": "Uniqueness", "severity": "Critical", "threshold": 0.0, "operator": "<="},
        {"rule_id": "DQ-COMPLETE", "rule_name": "Partition row coverage", "dimension": "Completeness", "severity": "Critical", "threshold": 0.90, "operator": ">="},
        {"rule_id": "DQ-VALID", "rule_name": "Required type validity", "dimension": "Validity", "severity": "High", "threshold": 0.0, "operator": "<="},
        {"rule_id": "DQ-TAXONOMY", "rule_name": "Unknown taxonomy rate", "dimension": "Consistency", "severity": "High", "threshold": 0.01, "operator": "<="},
        {"rule_id": "DQ-FRESH", "rule_name": "Freshness lag", "dimension": "Timeliness", "severity": "High", "threshold": 240.0, "operator": "<="},
        {"rule_id": "DQ-RECON", "rule_name": "Raw-to-dashboard variance", "dimension": "Reconciliation", "severity": "Critical", "threshold": 0.005, "operator": "<="},
    ]
    records = []
    pipeline_runs = []
    quality_results = []
    reliability_start = dt.date(2026, 3, 1)
    for day in date_range(reliability_start, SNAPSHOT_DATE):
        for asset in assets:
            asset_id = asset["asset_id"]
            expected_rows = 100
            actual_rows = 100
            freshness = rng.randint(55, 185)
            duplicate_count = 0
            invalid_count = 0
            unknown_count = 0
            reconciliation_variance = rng.uniform(0.0004, 0.0032)
            schema_version = "v1"
            if asset_id == "WEB_EVENTS" and day in (dt.date(2026, 4, 14), dt.date(2026, 4, 15)):
                duplicate_count = 6
                actual_rows = 106
                reconciliation_variance = 0.037
                schema_version = "v2-tracking"
            if asset_id == "CAMPAIGN_SPEND" and dt.date(2026, 5, 8) <= day <= dt.date(2026, 5, 10):
                unknown_count = 13
                reconciliation_variance = 0.012
                schema_version = "v2-channel"
            if asset_id == "CAMPAIGN_SPEND" and dt.date(2026, 6, 28) <= day <= SNAPSHOT_DATE:
                unknown_count = 2
                schema_version = "v3-governance-pending"
            if asset_id == "CRM_LEADS" and day == dt.date(2026, 6, 3):
                actual_rows = 58
                freshness = 520
                reconciliation_variance = 0.421
            if asset_id == "COMMERCE_ORDERS" and dt.date(2026, 6, 17) <= day <= dt.date(2026, 6, 18):
                invalid_count = 4
                reconciliation_variance = 0.021
                schema_version = "v2-order"
            run_id = f"RUN-{day.strftime('%Y%m%d')}-{asset_id}"
            pipeline_row = {
                "run_id": run_id, "run_date": day.isoformat(), "asset_id": asset_id,
                "scheduled_at": f"{day.isoformat()}T02:00:00Z",
                "completed_at": (dt.datetime.combine(day, dt.time(2, 0)) + dt.timedelta(minutes=freshness)).isoformat() + "Z",
                "freshness_minutes": freshness, "rows_expected": expected_rows, "rows_loaded": actual_rows,
                "pipeline_status": "SUCCEEDED", "schema_version": schema_version,
            }
            keys = [f"{asset_id}-{day.strftime('%Y%m%d')}-{index:03d}" for index in range(actual_rows)]
            if duplicate_count:
                for index in range(duplicate_count):
                    keys[-(index + 1)] = keys[index]
            run_records = []
            for index, business_key in enumerate(keys):
                is_unknown = 1 if index < unknown_count else 0
                is_valid = 0 if index < invalid_count else 1
                run_records.append({
                    "record_id": f"REC-{day.strftime('%Y%m%d')}-{asset_id}-{index:03d}",
                    "event_date": day.isoformat(), "asset_id": asset_id,
                    "business_key": business_key, "event_type": "purchase" if asset_id == "WEB_EVENTS" and index % 19 == 0 else "standard",
                    "numeric_value": round(20 + rng.random() * 480, 2),
                    "source_medium": "unknown/new-social" if is_unknown else "governed/source",
                    "schema_version": schema_version, "required_value_valid": is_valid,
                })
            records.extend(run_records)
            governed_value = round(sum(row["numeric_value"] for row in run_records), 2)
            dashboard_value = round(governed_value * (1 + reconciliation_variance), 2)
            reconciliation_variance = safe_div(
                abs(dashboard_value - governed_value), abs(governed_value)
            )
            pipeline_row.update({
                "governed_value": governed_value,
                "dashboard_value": dashboard_value,
            })
            pipeline_runs.append(pipeline_row)
            observations = {
                "DQ-UNIQUE": float(duplicate_count),
                "DQ-COMPLETE": actual_rows / expected_rows,
                "DQ-VALID": float(invalid_count),
                "DQ-TAXONOMY": unknown_count / actual_rows,
                "DQ-FRESH": float(freshness),
                "DQ-RECON": reconciliation_variance,
            }
            for rule in rules:
                observed = observations[rule["rule_id"]]
                passed = observed <= rule["threshold"] if rule["operator"] == "<=" else observed >= rule["threshold"]
                if passed:
                    status = "PASS"
                elif rule["severity"] == "Critical":
                    status = "FAIL"
                else:
                    status = "WARN"
                affected = duplicate_count if rule["rule_id"] == "DQ-UNIQUE" else (
                    max(0, expected_rows - actual_rows) if rule["rule_id"] == "DQ-COMPLETE" else (
                        invalid_count if rule["rule_id"] == "DQ-VALID" else (
                            unknown_count if rule["rule_id"] == "DQ-TAXONOMY" else (1 if not passed else 0)
                        )
                    )
                )
                quality_results.append({
                    "run_date": day.isoformat(), "run_id": run_id, "asset_id": asset_id,
                    "rule_id": rule["rule_id"], "rule_name": rule["rule_name"],
                    "quality_dimension": rule["dimension"], "severity": rule["severity"],
                    "observed_value": round(observed, 6), "threshold": rule["threshold"],
                    "operator": rule["operator"], "status": status, "affected_rows": affected,
                    "owner": asset["owner"],
                })

    changes = [
        {"change_id": "CHG-101", "title": "Purchase tracking schema", "priority": "P3", "ready_date": "2026-04-08", "release_date": "2026-04-14", "owner": "Web Analytics"},
        {"change_id": "CHG-102", "title": "Purchase deduplication repair", "priority": "P3", "ready_date": "2026-04-15", "release_date": "2026-04-17", "owner": "Analytics Engineering"},
        {"change_id": "CHG-103", "title": "Channel connector upgrade", "priority": "P4", "ready_date": "2026-04-27", "release_date": "2026-05-08", "owner": "Marketing Operations"},
        {"change_id": "CHG-104", "title": "Taxonomy mapping patch", "priority": "P3", "ready_date": "2026-05-09", "release_date": "2026-05-12", "owner": "Marketing Operations"},
        {"change_id": "CHG-105", "title": "CRM partition retry policy", "priority": "P3", "ready_date": "2026-06-03", "release_date": "2026-06-05", "owner": "Revenue Analytics"},
        {"change_id": "CHG-106", "title": "Order value type guard", "priority": "P3", "ready_date": "2026-06-17", "release_date": "2026-06-19", "owner": "Analytics Engineering"},
        {"change_id": "CHG-107", "title": "Acquisition dashboard refresh", "priority": "P4", "ready_date": "2026-06-24", "release_date": "2026-07-01", "owner": "BI Delivery"},
    ]
    release_specs = [
        ("REL-001", "2026-04-14", "2026-04-14"),
        ("REL-002", "2026-04-17", "2026-04-17"),
        ("REL-003", "2026-05-08", "2026-05-08"),
        ("REL-004", "2026-05-12", "2026-05-12"),
        ("REL-005", "2026-06-05", "2026-06-05"),
        ("REL-006", "2026-06-19", "2026-06-19"),
        ("REL-007", "2026-07-01", "2026-06-30"),
    ]
    releases = []
    for release_id, scheduled_date, evidence_date in release_specs:
        evidence_rows = [
            row for row in quality_results if row["run_date"] == evidence_date
        ]
        critical_failures = sum(
            row["severity"] == "Critical" and row["status"] == "FAIL"
            for row in evidence_rows
        )
        high_warnings = sum(
            row["severity"] == "High" and row["status"] == "WARN"
            for row in evidence_rows
        )
        caveated = release_id == "REL-007"
        releases.append({
            "release_id": release_id,
            "scheduled_date": scheduled_date,
            "evidence_date": evidence_date,
            "critical_failures": critical_failures,
            "high_warnings": high_warnings,
            "signoff_complete": 1,
            "rollback_ready": 1,
            "exceptions_accepted": 1 if caveated else 0,
            "exception_owner": "Marketing Operations" if caveated else "",
            "exception_expiry": "2026-07-15" if caveated else "",
            "exception_reason": (
                "Channel definition governance review pending"
                if caveated else ""
            ),
        })
    incidents = [
        {"incident_id": "INC-201", "asset_id": "WEB_EVENTS", "release_id": "REL-001", "started_at": "2026-04-14T09:00:00Z", "detected_at": "2026-04-14T10:15:00Z", "resolved_at": "2026-04-17T13:00:00Z", "severity": "Critical", "root_cause": "Duplicate tracking", "status": "Resolved"},
        {"incident_id": "INC-202", "asset_id": "CAMPAIGN_SPEND", "release_id": "REL-003", "started_at": "2026-05-08T02:00:00Z", "detected_at": "2026-05-08T05:30:00Z", "resolved_at": "2026-05-12T11:00:00Z", "severity": "High", "root_cause": "Taxonomy drift", "status": "Resolved"},
        {"incident_id": "INC-203", "asset_id": "CRM_LEADS", "release_id": "", "started_at": "2026-06-03T02:00:00Z", "detected_at": "2026-06-03T08:45:00Z", "resolved_at": "2026-06-05T09:00:00Z", "severity": "Critical", "root_cause": "Partial partition", "status": "Resolved"},
        {"incident_id": "INC-204", "asset_id": "COMMERCE_ORDERS", "release_id": "REL-006", "started_at": "2026-06-17T02:00:00Z", "detected_at": "2026-06-17T06:10:00Z", "resolved_at": "2026-06-19T16:00:00Z", "severity": "High", "root_cause": "Schema drift", "status": "Resolved"},
        {"incident_id": "INC-205", "asset_id": "CAMPAIGN_SPEND", "release_id": "REL-007", "started_at": "2026-06-28T08:00:00Z", "detected_at": "2026-06-28T11:00:00Z", "resolved_at": "", "severity": "High", "root_cause": "Channel definition governance", "status": "Accepted exception"},
    ]
    write_csv(project_dir / "data/raw/source_records.csv", list(records[0]), records)
    write_csv(project_dir / "data/raw/pipeline_runs.csv", list(pipeline_runs[0]), pipeline_runs)
    write_csv(project_dir / "data/raw/quality_results.csv", list(quality_results[0]), quality_results)
    write_csv(project_dir / "data/raw/change_requests.csv", list(changes[0]), changes)
    write_csv(project_dir / "data/raw/releases.csv", list(releases[0]), releases)
    write_csv(project_dir / "data/raw/incidents.csv", list(incidents[0]), incidents)
    write_json(project_dir / "data/scenario-manifest.json", {
        "synthetic": True, "seed": seed, "snapshot_date": SNAPSHOT_DATE.isoformat(),
        "injected_scenarios": [
            {"id": "ANOM-01", "asset": "WEB_EVENTS", "dates": ["2026-04-14", "2026-04-15"], "condition": "duplicate business keys", "linked_release": "REL-001"},
            {"id": "ANOM-02", "asset": "CAMPAIGN_SPEND", "dates": ["2026-05-08", "2026-05-09", "2026-05-10"], "condition": "unmapped channel taxonomy", "linked_release": "REL-003"},
            {"id": "ANOM-03", "asset": "CRM_LEADS", "dates": ["2026-06-03"], "condition": "partial and late partition", "linked_release": None},
            {"id": "ANOM-04", "asset": "COMMERCE_ORDERS", "dates": ["2026-06-17", "2026-06-18"], "condition": "required value type drift", "linked_release": "REL-006"},
            {"id": "ANOM-05", "asset": "CAMPAIGN_SPEND", "dates": ["2026-06-28", "2026-06-29", "2026-06-30"], "condition": "accepted channel-definition warning", "linked_release": "REL-007"},
        ],
    })

    con = sqlite3.connect(":memory:")
    load_sqlite_table(con, "fact_pipeline_run", pipeline_runs, [
        ("run_id", "TEXT"), ("run_date", "TEXT"), ("asset_id", "TEXT"), ("scheduled_at", "TEXT"),
        ("completed_at", "TEXT"), ("freshness_minutes", "INTEGER"), ("rows_expected", "INTEGER"),
        ("rows_loaded", "INTEGER"), ("pipeline_status", "TEXT"), ("schema_version", "TEXT"),
        ("governed_value", "REAL"), ("dashboard_value", "REAL"),
    ])
    load_sqlite_table(con, "fact_quality_result", quality_results, [
        ("run_date", "TEXT"), ("run_id", "TEXT"), ("asset_id", "TEXT"), ("rule_id", "TEXT"),
        ("rule_name", "TEXT"), ("quality_dimension", "TEXT"), ("severity", "TEXT"),
        ("observed_value", "REAL"), ("threshold", "REAL"), ("operator", "TEXT"),
        ("status", "TEXT"), ("affected_rows", "INTEGER"), ("owner", "TEXT"),
    ])
    load_sqlite_table(con, "fact_change_request", changes, [
        ("change_id", "TEXT"), ("title", "TEXT"), ("priority", "TEXT"), ("ready_date", "TEXT"),
        ("release_date", "TEXT"), ("owner", "TEXT"),
    ])
    load_sqlite_table(con, "fact_release", releases, [
        ("release_id", "TEXT"), ("scheduled_date", "TEXT"), ("evidence_date", "TEXT"),
        ("critical_failures", "INTEGER"),
        ("high_warnings", "INTEGER"), ("signoff_complete", "INTEGER"), ("rollback_ready", "INTEGER"),
        ("exceptions_accepted", "INTEGER"), ("exception_owner", "TEXT"),
        ("exception_expiry", "TEXT"), ("exception_reason", "TEXT"),
    ])
    load_sqlite_table(con, "fact_incident", incidents, [
        ("incident_id", "TEXT"), ("asset_id", "TEXT"), ("release_id", "TEXT"),
        ("started_at", "TEXT"), ("detected_at", "TEXT"), ("resolved_at", "TEXT"),
        ("severity", "TEXT"), ("root_cause", "TEXT"), ("status", "TEXT"),
    ])
    sql_summary = """
WITH latest_release AS (
  SELECT *, CASE
    WHEN critical_failures > 0 OR signoff_complete = 0 OR rollback_ready = 0 THEN 'HOLD'
    WHEN high_warnings BETWEEN 1 AND 2
         AND exceptions_accepted = 1
         AND exception_owner <> ''
         AND exception_expiry > scheduled_date THEN 'SHIP WITH CAVEAT'
    WHEN high_warnings = 0 THEN 'SHIP'
    ELSE 'HOLD' END AS release_decision
  FROM fact_release ORDER BY scheduled_date DESC LIMIT 1
), recent_quality AS (
  SELECT * FROM fact_quality_result WHERE run_date >= '2026-06-01'
), critical AS (
  SELECT SUM(CASE WHEN status = 'PASS' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS critical_pass_rate
  FROM recent_quality WHERE severity = 'Critical'
), freshness AS (
  SELECT SUM(CASE WHEN freshness_minutes <= 240 AND pipeline_status = 'SUCCEEDED' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS freshness_sla_rate
  FROM fact_pipeline_run WHERE run_date >= '2026-06-01'
), latest_recon AS (
  SELECT MAX(ABS(dashboard_value - governed_value) / ABS(governed_value))
         AS latest_reconciliation_variance
  FROM fact_pipeline_run WHERE run_date = '2026-06-30'
), open_incidents AS (
  SELECT COUNT(*) AS open_high_critical_incidents FROM fact_incident
  WHERE resolved_at = '' AND severity IN ('High', 'Critical')
), lead_time AS (
  SELECT AVG(julianday(release_date) - julianday(ready_date)) AS average_change_lead_days
  FROM fact_change_request WHERE release_date <= '2026-06-30'
)
SELECT release_decision, ROUND(critical_pass_rate, 6) AS critical_pass_rate,
       ROUND(freshness_sla_rate, 6) AS freshness_sla_rate,
       ROUND(latest_reconciliation_variance, 6) AS latest_reconciliation_variance,
       open_high_critical_incidents, ROUND(average_change_lead_days, 2) AS average_change_lead_days
FROM latest_release CROSS JOIN critical CROSS JOIN freshness CROSS JOIN latest_recon
CROSS JOIN open_incidents CROSS JOIN lead_time;
""".strip()
    sql_weekly = """
SELECT strftime('%Y-W%W', run_date) AS week,
       ROUND(SUM(CASE WHEN status = 'PASS' THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 6) AS pass_rate,
       SUM(CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END) AS failures,
       SUM(CASE WHEN status = 'WARN' THEN 1 ELSE 0 END) AS warnings
FROM fact_quality_result GROUP BY week ORDER BY week;
""".strip()
    sql_asset = """
SELECT asset_id,
       ROUND(SUM(CASE WHEN status = 'PASS' THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 6) AS pass_rate,
       SUM(CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END) AS failures,
       SUM(CASE WHEN status = 'WARN' THEN 1 ELSE 0 END) AS warnings
FROM fact_quality_result GROUP BY asset_id ORDER BY pass_rate ASC;
""".strip()
    sql_recon = """
SELECT asset_id,
       ROUND(ABS(dashboard_value - governed_value) / ABS(governed_value), 6)
       AS reconciliation_variance,
       ROUND(ABS(dashboard_value - governed_value) / ABS(governed_value) * 10000, 2)
       AS reconciliation_variance_bps
FROM fact_pipeline_run WHERE run_date = '2026-06-30'
ORDER BY reconciliation_variance DESC;
""".strip()
    sql_failures = """
SELECT run_date, asset_id, rule_name, severity, status, observed_value, threshold, affected_rows, owner
FROM fact_quality_result WHERE status <> 'PASS'
ORDER BY run_date DESC, CASE severity WHEN 'Critical' THEN 1 ELSE 2 END LIMIT 30;
""".strip()
    sql_releases = """
SELECT release_id, scheduled_date, evidence_date, critical_failures, high_warnings,
       exception_owner, exception_expiry,
       CASE
         WHEN critical_failures > 0 OR signoff_complete = 0 OR rollback_ready = 0 THEN 'HOLD'
         WHEN high_warnings BETWEEN 1 AND 2
              AND exceptions_accepted = 1
              AND exception_owner <> ''
              AND exception_expiry > scheduled_date THEN 'SHIP WITH CAVEAT'
         WHEN high_warnings = 0 THEN 'SHIP'
         ELSE 'HOLD' END AS decision
FROM fact_release ORDER BY scheduled_date DESC;
""".strip()
    sql_incident = """
SELECT root_cause, COUNT(*) AS incidents,
       SUM(CASE WHEN severity = 'Critical' THEN 1 ELSE 0 END) AS critical_incidents
FROM fact_incident GROUP BY root_cause ORDER BY incidents DESC, root_cause;
""".strip()
    summary = query_rows(con, sql_summary)
    weekly = query_rows(con, sql_weekly)
    asset_quality = query_rows(con, sql_asset)
    reconciliation = query_rows(con, sql_recon)
    failure_evidence = query_rows(con, sql_failures)
    release_gate = query_rows(con, sql_releases)
    incident_causes = query_rows(con, sql_incident)
    con.close()
    datasets = {
        "summary": summary, "weekly_quality": weekly, "asset_quality": asset_quality,
        "reconciliation": reconciliation, "failure_evidence": failure_evidence,
        "release_gate": release_gate, "incident_causes": incident_causes,
    }
    for name, rows in datasets.items():
        if rows:
            write_csv(project_dir / f"data/curated/{name}.csv", list(rows[0]), rows)
    write_json(project_dir / "data/curated/dashboard-data.json", datasets)
    write_json(project_dir / "data/curated/summary.json", summary[0])
    sql_all = "\n\n".join([
        "-- Executive release decision\n" + sql_summary,
        "-- Weekly quality trend\n" + sql_weekly,
        "-- Asset quality\n" + sql_asset,
        "-- Latest reconciliation\n" + sql_recon,
        "-- Failure evidence\n" + sql_failures,
        "-- Release gates\n" + sql_releases,
        "-- Incident root causes\n" + sql_incident,
    ])
    write_text(project_dir / "sql/analytics.sql", sql_all)
    write_text(project_dir / "sql/tests.sql", """
-- Expected to return zero rows outside the documented anomaly windows.
SELECT run_id, rule_id, COUNT(*) FROM fact_quality_result GROUP BY 1,2 HAVING COUNT(*) <> 1;
SELECT * FROM fact_pipeline_run WHERE rows_loaded < 0 OR freshness_minutes < 0;
SELECT * FROM fact_quality_result
WHERE (operator = '<=' AND status = 'PASS' AND observed_value > threshold)
   OR (operator = '>=' AND status = 'PASS' AND observed_value < threshold);

SELECT q.run_id
FROM fact_quality_result q JOIN fact_pipeline_run p USING (run_id)
WHERE q.rule_id = 'DQ-RECON'
  AND ABS(q.observed_value - ABS(p.dashboard_value - p.governed_value) / ABS(p.governed_value)) > 0.000001;

WITH observed AS (
  SELECT r.release_id,
         SUM(CASE WHEN q.severity = 'Critical' AND q.status = 'FAIL' THEN 1 ELSE 0 END) AS critical_failures,
         SUM(CASE WHEN q.severity = 'High' AND q.status = 'WARN' THEN 1 ELSE 0 END) AS high_warnings
  FROM fact_release r JOIN fact_quality_result q ON q.run_date = r.evidence_date
  GROUP BY r.release_id
)
SELECT r.release_id FROM fact_release r JOIN observed o USING (release_id)
WHERE r.critical_failures <> o.critical_failures OR r.high_warnings <> o.high_warnings;

SELECT * FROM fact_release
WHERE exceptions_accepted = 1
  AND (exception_owner = '' OR exception_expiry <= scheduled_date);
""")
    current = summary[0]
    notebook = execute_notebook(project_dir, [
        ("markdown", f"""# Analytics Reliability & Release Control\n\n## tl;dr\n\nThe candidate release decision is **{current['release_decision']}**. Critical controls pass at **{current['critical_pass_rate']:.1%}**, freshness SLA compliance is **{current['freshness_sla_rate']:.1%}**, and one accepted high-severity exception remains open.\n"""),
        ("markdown", """## Context & Methods\n\nDecision: ship, hold, or ship with a caveat. The raw layer contains five disclosed, deterministic anomaly scenarios. Release status is a gate, not a weighted trust score.\n\n### Key Assumptions\n\n- Critical failures always block.\n- A high warning can ship only with an owner, future expiry and accepted exception.\n- Every release records the quality-evidence date used to derive its failure and warning counts.\n- The latest complete synthetic snapshot is 30 Jun 2026.\n"""),
        ("code", """from pathlib import Path\nimport csv, json\nPROJECT_DIR = Path.cwd()\ndef read_csv(name):\n    with (PROJECT_DIR / name).open(encoding='utf-8') as handle:\n        return list(csv.DictReader(handle))\nsummary = json.loads((PROJECT_DIR / 'data/curated/summary.json').read_text())\nfailures = read_csv('data/curated/failure_evidence.csv')\nprint(json.dumps(summary, indent=2))\nprint(f\"reviewable failure/warning rows={len(failures)}\")\n"""),
        ("markdown", """## Data\n\nThe control plane uses one row per scheduled asset run and one row per run × quality rule. Raw records remain inspectable and intentional scenario anomalies are separately declared.\n"""),
        ("code", """quality = read_csv('data/raw/quality_results.csv')\nstatus_counts = {}\nfor row in quality:\n    status_counts[row['status']] = status_counts.get(row['status'], 0) + 1\nprint(f\"quality results={len(quality):,} | status counts={status_counts}\")\n"""),
        ("markdown", """## Results\n\nFailures are localized by asset, date, rule, severity and owner. This makes a release decision inspectable instead of relying on a cosmetic health score.\n"""),
        ("code", """for row in failures[:12]:\n    print(f\"{row['run_date']} | {row['asset_id']:<18} | {row['status']:<4} | {row['rule_name']} | observed={row['observed_value']} threshold={row['threshold']}\")\n"""),
        ("markdown", """## Takeaways\n\n1. The synthetic release can ship only with the documented, owned high-severity caveat.\n2. Critical uniqueness, completeness and reconciliation failures remain hard blockers.\n3. Each anomaly is traceable from raw evidence through rule result, incident and remediation release.\n"""),
    ])
    write_json(project_dir / "notebooks/analysis.ipynb", notebook)

    definitions = [
        "Critical Pass Rate = passed critical tests / executed critical tests in Jun 2026.",
        "Freshness SLA = successful scheduled runs completed within 240 minutes / all scheduled runs in Jun 2026.",
        "Reconciliation Variance = ABS(dashboard value - governed raw value) / ABS(governed raw value).",
        "Average Change Lead Time = average days from ready date to release date for released changes.",
        "Open High/Critical Incidents = unresolved incidents whose severity is High or Critical.",
        "Release gate: HOLD on critical failure or missing signoff/rollback; caveated ship requires accepted high warnings with an owner and expiry after the scheduled release.",
    ]
    source_specs = []
    for source_id, label, sql, tables in [
        (
            "rel_summary",
            "Release decision",
            sql_summary,
            ["fact_release", "fact_quality_result", "fact_pipeline_run", "fact_incident", "fact_change_request"],
        ),
        ("rel_weekly", "Weekly quality trend", sql_weekly, ["fact_quality_result"]),
        ("rel_asset", "Asset quality", sql_asset, ["fact_quality_result"]),
        ("rel_recon", "Latest reconciliation", sql_recon, ["fact_pipeline_run"]),
        ("rel_failures", "Failure evidence", sql_failures, ["fact_quality_result"]),
        ("rel_releases", "Release gates", sql_releases, ["fact_release"]),
        ("rel_incidents", "Incident root causes", sql_incident, ["fact_incident"]),
    ]:
        source_specs.append(artifact_source(
            source_id, label, sql, tables,
            definitions, "sql/analytics.sql", ["Synthetic data", "Snapshot through 2026-06-30"],
        ))
    cards = [
        make_card("release_decision", "summary", "rel_summary", "Release decision", "release_decision", description="Hard gate derived from failures, signoff, rollback and accepted exceptions."),
        make_card("critical_pass", "summary", "rel_summary", "Critical pass rate", "critical_pass_rate", "percent", "Passed critical controls divided by executed critical controls in June."),
        make_card("freshness", "summary", "rel_summary", "Freshness SLA", "freshness_sla_rate", "percent", "Scheduled June runs completed successfully within four hours."),
        make_card("recon", "summary", "rel_summary", "Latest max variance", "latest_reconciliation_variance", "percent", "Highest raw-to-dashboard variance on the snapshot date."),
        make_card("open_incidents", "summary", "rel_summary", "Open high/critical", "open_high_critical_incidents", "number", "Unresolved incidents whose severity is High or Critical."),
        make_card("lead_time", "summary", "rel_summary", "Avg change lead days", "average_change_lead_days", "number", "Ready-to-release days for completed changes."),
    ]
    charts = [
        make_chart("weekly_quality", "Quality test pass rate by week", "line", "weekly_quality", "rel_weekly", "week", "pass_rate", subtitle="All executed tests; warnings are not passes", fmt="percent", layout="full"),
        make_chart("asset_quality", "Quality pass rate by asset", "horizontalBar", "asset_quality", "rel_asset", "asset_id", "pass_rate", subtitle="Complete Mar–Jun synthetic period", fmt="percent"),
        make_chart(
            "latest_recon",
            "Latest reconciliation variance by asset",
            "horizontalBar",
            "reconciliation",
            "rel_recon",
            "asset_id",
            "reconciliation_variance_bps",
            subtitle="Basis points (bp) on 30 Jun 2026 · critical threshold 50 bp",
            fmt="number",
        ),
    ]
    tables = [
        {
            "id": "incident_table", "title": "Incidents by root-cause category",
            "subtitle": "Documented synthetic scenarios",
            "dataset": "incident_causes", "sourceId": "rel_incidents", "layout": "full", "density": "dense",
            "defaultSort": {"field": "incidents", "direction": "desc"},
            "columns": [
                {"field": "root_cause", "label": "Root cause", "type": "text"},
                {"field": "incidents", "label": "Incidents", "format": "number"},
                {"field": "critical_incidents", "label": "Critical", "format": "number"},
            ],
        },
        {
            "id": "release_table", "title": "Release gate history", "dataset": "release_gate",
            "sourceId": "rel_releases", "layout": "full", "density": "dense",
            "defaultSort": {"field": "scheduled_date", "direction": "desc"},
            "columns": [
                {"field": "release_id", "label": "Release", "type": "text"},
                {"field": "scheduled_date", "label": "Scheduled", "type": "date"},
                {"field": "evidence_date", "label": "Evidence date", "type": "date"},
                {"field": "critical_failures", "label": "Critical failures", "format": "number"},
                {"field": "high_warnings", "label": "High warnings", "format": "number"},
                {"field": "exception_owner", "label": "Exception owner", "type": "text"},
                {"field": "exception_expiry", "label": "Exception expiry", "type": "date"},
                {"field": "decision", "label": "Decision", "type": "text"},
            ],
        },
        {
            "id": "failure_table", "title": "Failure and warning evidence", "dataset": "failure_evidence",
            "sourceId": "rel_failures", "layout": "full", "density": "dense",
            "defaultSort": {"field": "run_date", "direction": "desc"},
            "columns": [
                {"field": "run_date", "label": "Date", "type": "date"},
                {"field": "asset_id", "label": "Asset", "type": "text"},
                {"field": "rule_name", "label": "Rule", "type": "text"},
                {"field": "severity", "label": "Severity", "type": "text"},
                {"field": "status", "label": "Status", "type": "text"},
                {"field": "affected_rows", "label": "Affected", "format": "number"},
                {"field": "owner", "label": "Owner", "type": "text"},
            ],
        },
    ]
    blocks = [
        {"id": "intro", "type": "markdown", "body": "# Analytics Reliability & Release Control\n\n**Decision:** should the next analytics release ship, be held, or ship with an explicitly accepted caveat?\n\n*Deterministic synthetic portfolio data · snapshot 30 Jun 2026 · raw anomalies are disclosed in the scenario manifest.*"},
        {"id": "metrics", "type": "metric-strip", "cardIds": [item["id"] for item in cards]},
        {"id": "weekly", "type": "chart", "chartId": "weekly_quality", "layout": "full"},
        {"id": "asset", "type": "chart", "chartId": "asset_quality", "layout": "half"},
        {"id": "recon", "type": "chart", "chartId": "latest_recon", "layout": "half"},
        {"id": "causes", "type": "table", "tableId": "incident_table", "layout": "full"},
        {"id": "releases", "type": "table", "tableId": "release_table", "layout": "full"},
        {"id": "failures", "type": "table", "tableId": "failure_table", "layout": "full"},
        {"id": "method", "type": "markdown", "body": "## Gate, evidence and limitations\n\nThe dashboard deliberately avoids an opaque trust score. A critical failure blocks release. A high warning can ship only with an accepted, owned, expiring caveat. All issues and resolutions are fictional and exist only to demonstrate quality and release-governance methods."},
    ]
    artifact_manifest = {
        "version": 1, "surface": "dashboard", "title": "Analytics Reliability & Release Control",
        "description": "Synthetic analytics quality, reconciliation and release-governance dashboard.",
        "generatedAt": GENERATED_AT, "cards": cards, "charts": charts, "tables": tables, "blocks": blocks,
    }
    write_text(project_dir / "README.md", f"""
# Analytics Reliability & Release Control

Analytics delivery and data-quality portfolio project using deterministic synthetic data.

## Decision

Should the next analytics release ship, be held, or ship with an explicitly accepted caveat?

## Reproduce

```bash
python3 scripts/build_analytics_projects.py --project reliability
python3 scripts/validate_portfolio_data.py --project reliability
```

- Source records: {len(records):,}
- Quality results: {len(quality_results):,}
- Period: 1 Mar–30 Jun 2026
- Seed: {seed}
- SQL: `sql/analytics.sql`
- Executed notebook: `notebooks/analysis.ipynb`
- Scenario disclosure: `data/scenario-manifest.json`

No employer policy, data or release is represented.
""")
    write_text(project_dir / "docs/metric-dictionary.md", "# Metric dictionary\n\n" + "\n".join(f"- {item}" for item in definitions))
    write_text(project_dir / "docs/data-contract.md", """
# Data contract

- Pipeline grain: one row per scheduled date × asset.
- Quality grain: one row per pipeline run × quality rule.
- Required dimensions: asset, run date, rule, severity, threshold, owner and evidence path.
- Critical thresholds: no duplicate business keys, at least 90% partition coverage and no more than 0.5% reconciliation variance.
- A missing partition is not treated as a healthy zero.
""")
    write_text(project_dir / "docs/data-dictionary.md", """
# Data dictionary

- `source_records.csv`: inspectable synthetic raw evidence.
- `pipeline_runs.csv`: run grain, freshness, volume, schema version, governed value and dashboard value used for reconciliation.
- `quality_results.csv`: executed control evidence.
- `change_requests.csv`: ready-to-release delivery records.
- `releases.csv`: gate inputs; decision is derived in SQL.
- `incidents.csv`: start, detection, resolution, severity and linked release.
""")
    write_text(project_dir / "docs/incident-postmortem.md", """
# Synthetic incident postmortem: duplicate purchase tracking

The scenario injects duplicate business keys after `REL-001`. The uniqueness and reconciliation controls fail, the release gate resolves to HOLD, raw evidence is retained, and `REL-002` represents the remediation. This is a deterministic demonstration, not a real production incident.
""")
    write_text(project_dir / "docs/release-checklist.md", """
# Release checklist

- [ ] No critical control failure
- [ ] Data freshness and partitions complete
- [ ] Raw, curated and dashboard values reconcile
- [ ] Required stakeholder signoff recorded
- [ ] Rollback plan ready for high-risk changes
- [ ] Every accepted warning has an owner and expiry
""")
    write_text(project_dir / "docs/qa-report.md", """
# QA report

The build and independent validator check one result per run/rule, threshold/status consistency, timestamp order, raw anomaly detection, governed-to-dashboard reconciliation, release evidence counts, exception owner/expiry, release-gate derivation and dashboard/SQL reconciliation. Expected raw anomalies are enumerated in `data/scenario-manifest.json`.
""")
    receipt = build_artifact(project_dir, artifact_manifest, datasets, source_specs)
    manifest_for(project_dir, seed, "reliability-v1")
    return {"project": "reliability", "rows": len(records), "receipt": receipt, "summary": current}


def build_integration(project_dir: Path):
    seed = 43003
    rng = random.Random(seed)
    reset_project(project_dir)
    connector_types = [
        {"connector_id": "CRM", "connector_name": "CRM Cloud", "auth_type": "OAuth 2.0", "source_category": "CRM"},
        {"connector_id": "BILLING", "connector_name": "Billing API", "auth_type": "API key", "source_category": "Billing"},
        {"connector_id": "PRODUCT", "connector_name": "Product Events", "auth_type": "Bearer token", "source_category": "Product analytics"},
        {"connector_id": "WAREHOUSE", "connector_name": "Cloud Warehouse", "auth_type": "Service account", "source_category": "Data warehouse"},
    ]
    milestone_names = [
        "Discovery complete", "Authentication", "Mapping approved", "First test sync",
        "UAT complete", "Training", "Go-live", "First value",
    ]
    accounts = []
    account_connectors = []
    milestones = []
    mappings = []
    uat_results = []
    integration_runs = []
    blockers = []
    usage_rows = []
    start = dt.date(2025, 8, 1)
    account_meta = {}
    for index in range(1, 61):
        account_id = f"ACCT-{index:03d}"
        kickoff = start + dt.timedelta(days=(index - 1) * 5 + (index % 3))
        if index % 5 == 0:
            segment, base_days, complexity, connector_count = "Enterprise", 78, 3, 4
        elif index % 3 == 0:
            segment, base_days, complexity, connector_count = "Mid-Market", 55, 2, 3
        else:
            segment, base_days, complexity, connector_count = "SMB", 39, 1, 2
        committed = kickoff + dt.timedelta(days=base_days)
        template_cohort = "Standardized template" if kickoff >= dt.date(2026, 1, 15) else "Legacy mapping"
        template_gain = 6 if template_cohort == "Standardized template" else 0
        injected_delay = {14: 14, 21: 10, 39: 12, 52: 18, 57: 17, 58: 14, 59: 19, 60: 18}.get(index, 0)
        delivery_variation = rng.randint(-4, 8) + injected_delay - template_gain
        projected_go_live = kickoff + dt.timedelta(days=max(25, base_days + delivery_variation))
        actual_go_live = projected_go_live if projected_go_live <= SNAPSHOT_DATE else None
        project_status = "Completed" if actual_go_live else "Active"
        account_meta[account_id] = {
            "index": index, "kickoff": kickoff, "committed": committed,
            "projected": projected_go_live, "actual": actual_go_live,
            "segment": segment, "complexity": complexity, "base_days": base_days,
            "template_cohort": template_cohort,
        }
        assigned = connector_types[:connector_count]
        for connector in assigned:
            auth_date = kickoff + dt.timedelta(days=8 + complexity * 2 + connector_count)
            account_connectors.append({
                "account_id": account_id, "connector_id": connector["connector_id"],
                "connector_name": connector["connector_name"], "auth_type": connector["auth_type"],
                "environment": "Production", "authorized_at": auth_date.isoformat(),
                "schema_version": "v2" if kickoff >= dt.date(2026, 1, 1) else "v1",
            })
        # Planned and actual milestone dates use one coherent lifecycle.
        stage_fractions = [0.12, 0.24, 0.43, 0.55, 0.72, 0.84, 1.0, 1.14]
        milestone_actuals = {}
        for position, (name, fraction) in enumerate(zip(milestone_names, stage_fractions)):
            planned = kickoff + dt.timedelta(days=round(base_days * fraction))
            actual_candidate = kickoff + dt.timedelta(days=round(max(25, base_days + delivery_variation) * fraction))
            actual_date = actual_candidate if actual_candidate <= SNAPSHOT_DATE else None
            if name == "Go-live":
                actual_date = actual_go_live
            if name == "First value":
                # First value is set only after the usage acceptance conditions
                # are evaluated below; there is one canonical lifecycle date.
                actual_date = None
            milestone_actuals[name] = actual_date
            milestones.append({
                "account_id": account_id, "milestone": name, "stage_order": position + 1,
                "planned_date": planned.isoformat(), "actual_date": actual_date.isoformat() if actual_date else "",
                "status": "Complete" if actual_date else ("Late" if planned < SNAPSHOT_DATE else "Planned"),
                "owner": "Implementation" if name not in ("Authentication", "First test sync") else "Integration Engineering",
            })
        # Required mapping fields are evaluated at the project snapshot.
        progress = min(1.0, max(0.0, (SNAPSHOT_DATE - kickoff).days / max(1, (projected_go_live - kickoff).days)))
        for connector in assigned:
            for field_index, target_field in enumerate(("account_id", "event_time", "source_id", "metric_name", "metric_value", "currency")):
                if actual_go_live:
                    mapped = True
                else:
                    mapped = progress > (0.42 + field_index * 0.075)
                    if index in (57, 58, 59, 60) and field_index >= 4:
                        mapped = False
                mappings.append({
                    "account_id": account_id, "connector_id": connector["connector_id"],
                    "target_field": target_field, "source_field": f"src_{target_field}" if mapped else "",
                    "is_required": 1, "mapping_status": "Mapped" if mapped else "Missing",
                    "validated_at": SNAPSHOT_DATE.isoformat(),
                })
        # Eight required UAT cases; unexecuted cases stay in the readiness denominator.
        uat_progress = min(1.0, max(0.0, (progress - 0.55) / 0.35))
        for case_index in range(1, 9):
            executed = actual_go_live is not None or case_index <= round(8 * uat_progress)
            passed = executed and not (index in (57, 59, 60) and case_index >= 6)
            uat_results.append({
                "account_id": account_id, "uat_case_id": f"UAT-{case_index:02d}",
                "business_process": ["Authentication", "Mapping", "Historical load", "Incremental sync", "Retries", "Timezone", "Dashboard", "Handoff"][case_index - 1],
                "required_flag": 1, "executed_at": (kickoff + dt.timedelta(days=round(base_days * 0.70) + case_index)).isoformat() if executed else "",
                "status": "Passed" if passed else ("Failed" if executed else "Not executed"),
                "defect_severity": "High" if executed and not passed else "",
            })
        # Sync history continues after go-live, supporting implementation and hypercare analysis.
        for connector in assigned:
            current_day = kickoff + dt.timedelta(days=12)
            while current_day <= SNAPSHOT_DATE:
                received = rng.randint(720, 1680)
                rejected = rng.randint(0, max(1, round(received * 0.008)))
                status = "SUCCESS"
                http_status = 200
                retry_count = 0
                error_code = ""
                latency_ms = rng.randint(500, 3400)
                if connector["connector_id"] == "CRM" and index in (14, 21, 39) and dt.date(2026, 4, 10) <= current_day <= dt.date(2026, 4, 13):
                    status, http_status, error_code, retry_count = "FAILED", 401, "OAUTH_TOKEN_EXPIRED", 1
                    rejected = received
                elif connector["connector_id"] == "BILLING" and index % 4 == 0 and dt.date(2026, 5, 5) <= current_day <= dt.date(2026, 5, 11):
                    status, http_status, error_code, retry_count = "FAILED", 422, "SCHEMA_FIELD_CHANGED", 0
                    rejected = round(received * 0.24)
                elif connector["connector_id"] == "WAREHOUSE" and index % 5 == 0 and dt.date(2026, 5, 20) <= current_day <= dt.date(2026, 5, 23):
                    status, http_status, error_code, retry_count = "FAILED", 429, "RATE_LIMITED", 3
                    rejected = received
                    latency_ms = rng.randint(8000, 18000)
                elif rng.random() < 0.012:
                    status, http_status, error_code, retry_count = "FAILED", 503, "UPSTREAM_UNAVAILABLE", 2
                    rejected = received
                accepted = received - rejected
                integration_runs.append({
                    "run_id": f"SYNC-{account_id}-{connector['connector_id']}-{current_day.strftime('%Y%m%d')}",
                    "run_date": current_day.isoformat(), "account_id": account_id,
                    "connector_id": connector["connector_id"], "environment": "Production",
                    "status": status, "http_status": http_status, "records_received": received,
                    "records_accepted": accepted, "records_rejected": rejected,
                    "latency_ms": latency_ms, "retry_count": retry_count, "error_code": error_code,
                })
                current_day += dt.timedelta(days=3)
        if actual_go_live:
            for offset in range(30):
                usage_date = actual_go_live + dt.timedelta(days=offset)
                if usage_date > SNAPSHOT_DATE:
                    break
                active_users = max(1, min(8, 1 + offset // 3 + index % 3))
                success_syncs = 1 if offset >= 2 else 0
                acceptance = 0.96 if offset >= 4 else 0.91
                workflows = 1 if offset >= 5 else 0
                usage_rows.append({
                    "account_id": account_id, "usage_date": usage_date.isoformat(),
                    "active_users": active_users, "successful_syncs": success_syncs,
                    "data_acceptance_rate": acceptance, "key_workflows_completed": workflows,
                })

    # Derive readiness and risk from source records; no opaque status is authored manually.
    mapping_by_account = defaultdict(list)
    for row in mappings:
        mapping_by_account[row["account_id"]].append(row)
    uat_by_account = defaultdict(list)
    for row in uat_results:
        uat_by_account[row["account_id"]].append(row)
    runs_by_account = defaultdict(list)
    for row in integration_runs:
        runs_by_account[row["account_id"]].append(row)
    usage_by_account = defaultdict(list)
    for row in usage_rows:
        usage_by_account[row["account_id"]].append(row)
    first_value_milestones = {
        row["account_id"]: row
        for row in milestones
        if row["milestone"] == "First value"
    }
    for account_id, meta in account_meta.items():
        mapping_rows = mapping_by_account[account_id]
        mapping_coverage = safe_div(sum(row["mapping_status"] == "Mapped" for row in mapping_rows), len(mapping_rows))
        uat_rows = uat_by_account[account_id]
        uat_pass_rate = safe_div(sum(row["status"] == "Passed" for row in uat_rows), len(uat_rows))
        recent_runs = [row for row in runs_by_account[account_id] if row["run_date"] >= "2026-06-24"]
        integration_success = safe_div(sum(row["status"] == "SUCCESS" for row in recent_runs), len(recent_runs), 1.0)
        days_to_go_live = (meta["committed"] - SNAPSHOT_DATE).days
        if meta["actual"]:
            risk_status, risk_reason, next_action = "Green", "Implementation completed", "Monitor first-value adoption"
        elif days_to_go_live <= 14 and (mapping_coverage < 0.95 or uat_pass_rate < 0.90):
            risk_status, risk_reason, next_action = "Red", "Go-live ≤14 days with incomplete mapping or UAT", "Run daily recovery plan with decision owner"
        elif (
            mapping_coverage < 0.95
            or uat_pass_rate < 0.90
            or integration_success < 0.98
            or days_to_go_live < 22
        ):
            risk_status, risk_reason, next_action = "Amber", "Readiness, reliability or schedule guardrail at risk", "Resolve blocker and re-baseline remaining milestones"
        else:
            risk_status, risk_reason, next_action = "Green", "Readiness guardrails satisfied", "Continue planned delivery"
        first_value_dates = [
            dt.date.fromisoformat(row["usage_date"]) for row in usage_by_account[account_id]
            if row["active_users"] >= 3 and row["successful_syncs"] >= 1
            and row["data_acceptance_rate"] >= 0.95 and row["key_workflows_completed"] >= 1
        ]
        first_value_date = min(first_value_dates) if first_value_dates else None
        ttfv_days = (first_value_date - meta["kickoff"]).days if first_value_date else None
        first_value_milestone = first_value_milestones[account_id]
        first_value_milestone["actual_date"] = (
            first_value_date.isoformat() if first_value_date else ""
        )
        first_value_milestone["status"] = (
            "Complete"
            if first_value_date
            else (
                "Late"
                if dt.date.fromisoformat(first_value_milestone["planned_date"])
                < SNAPSHOT_DATE
                else "Planned"
            )
        )
        readiness = 0.4 * mapping_coverage + 0.3 * uat_pass_rate + 0.3 * integration_success
        account = {
            "account_id": account_id, "fictional_account_name": f"Demo Account {meta['index']:02d}",
            "segment": meta["segment"], "region": ["North", "South", "Central", "West"][meta["index"] % 4],
            "complexity_band": ["", "Standard", "Advanced", "Complex"][meta["complexity"]],
            "kickoff_date": meta["kickoff"].isoformat(), "committed_go_live_date": meta["committed"].isoformat(),
            "actual_go_live_date": meta["actual"].isoformat() if meta["actual"] else "",
            "projected_go_live_date": meta["projected"].isoformat(),
            "project_status": "Completed" if meta["actual"] else "Active",
            "template_cohort": meta["template_cohort"], "mapping_coverage": round(mapping_coverage, 6),
            "uat_pass_rate": round(uat_pass_rate, 6), "recent_integration_success_rate": round(integration_success, 6),
            "readiness_rate": round(readiness, 6), "days_to_committed_go_live": days_to_go_live,
            "risk_status": risk_status, "risk_reason": risk_reason, "next_action": next_action,
            "first_value_date": first_value_date.isoformat() if first_value_date else "",
            "time_to_first_value_days": ttfv_days if ttfv_days is not None else "",
        }
        accounts.append(account)
        if risk_status in ("Red", "Amber") and account["project_status"] == "Active":
            blockers.append({
                "ticket_id": f"BLK-{meta['index']:03d}", "account_id": account_id,
                "created_at": (SNAPSHOT_DATE - dt.timedelta(days=4 + meta["index"] % 6)).isoformat(),
                "severity": "High" if risk_status == "Red" else "Medium",
                "category": "Mapping/UAT readiness" if mapping_coverage < 0.95 else "Schedule/reliability",
                "status": "Open", "owner": "Implementation",
                "next_action": next_action,
            })

    write_csv(project_dir / "data/raw/accounts.csv", list(accounts[0]), accounts)
    write_csv(project_dir / "data/raw/account_connectors.csv", list(account_connectors[0]), account_connectors)
    write_csv(project_dir / "data/raw/milestones.csv", list(milestones[0]), milestones)
    write_csv(project_dir / "data/raw/integration_runs.csv", list(integration_runs[0]), integration_runs)
    write_csv(project_dir / "data/raw/mapping_validation.csv", list(mappings[0]), mappings)
    write_csv(project_dir / "data/raw/uat_results.csv", list(uat_results[0]), uat_results)
    write_csv(project_dir / "data/raw/blockers.csv", list(blockers[0]), blockers)
    write_csv(project_dir / "data/raw/usage_daily.csv", list(usage_rows[0]), usage_rows)
    write_json(project_dir / "data/scenario-manifest.json", {
        "synthetic": True, "seed": seed, "snapshot_date": SNAPSHOT_DATE.isoformat(),
        "injected_scenarios": [
            {"id": "INT-01", "condition": "OAuth token expiry", "error_code": "OAUTH_TOKEN_EXPIRED", "http_status": 401},
            {"id": "INT-02", "condition": "Billing schema drift", "error_code": "SCHEMA_FIELD_CHANGED", "http_status": 422},
            {"id": "INT-03", "condition": "Warehouse rate limit", "error_code": "RATE_LIMITED", "http_status": 429},
            {"id": "INT-04", "condition": "Active accounts crossing schedule, mapping, UAT or reliability guardrails", "accounts": ["ACCT-055", "ACCT-057", "ACCT-058", "ACCT-059", "ACCT-060"]},
        ],
    })

    con = sqlite3.connect(":memory:")
    load_sqlite_table(con, "dim_account", accounts, [
        ("account_id", "TEXT"), ("fictional_account_name", "TEXT"), ("segment", "TEXT"), ("region", "TEXT"),
        ("complexity_band", "TEXT"), ("kickoff_date", "TEXT"), ("committed_go_live_date", "TEXT"),
        ("actual_go_live_date", "TEXT"), ("projected_go_live_date", "TEXT"), ("project_status", "TEXT"),
        ("template_cohort", "TEXT"), ("mapping_coverage", "REAL"), ("uat_pass_rate", "REAL"),
        ("recent_integration_success_rate", "REAL"), ("readiness_rate", "REAL"),
        ("days_to_committed_go_live", "INTEGER"), ("risk_status", "TEXT"), ("risk_reason", "TEXT"),
        ("next_action", "TEXT"), ("first_value_date", "TEXT"), ("time_to_first_value_days", "INTEGER"),
    ])
    load_sqlite_table(con, "fact_integration_run", integration_runs, [
        ("run_id", "TEXT"), ("run_date", "TEXT"), ("account_id", "TEXT"), ("connector_id", "TEXT"),
        ("environment", "TEXT"), ("status", "TEXT"), ("http_status", "INTEGER"),
        ("records_received", "INTEGER"), ("records_accepted", "INTEGER"), ("records_rejected", "INTEGER"),
        ("latency_ms", "INTEGER"), ("retry_count", "INTEGER"), ("error_code", "TEXT"),
    ])
    load_sqlite_table(con, "fact_milestone", milestones, [
        ("account_id", "TEXT"), ("milestone", "TEXT"), ("stage_order", "INTEGER"),
        ("planned_date", "TEXT"), ("actual_date", "TEXT"), ("status", "TEXT"), ("owner", "TEXT"),
    ])
    load_sqlite_table(con, "fact_blocker", blockers, [
        ("ticket_id", "TEXT"), ("account_id", "TEXT"), ("created_at", "TEXT"), ("severity", "TEXT"),
        ("category", "TEXT"), ("status", "TEXT"), ("owner", "TEXT"), ("next_action", "TEXT"),
    ])
    sql_summary = """
WITH completed AS (
  SELECT *, julianday(actual_go_live_date) - julianday(kickoff_date) AS lead_days
  FROM dim_account WHERE project_status = 'Completed'
), ordered_ttfv AS (
  SELECT time_to_first_value_days,
         ROW_NUMBER() OVER (ORDER BY time_to_first_value_days) AS row_number,
         COUNT(*) OVER () AS total_rows
  FROM dim_account WHERE time_to_first_value_days IS NOT NULL AND time_to_first_value_days <> ''
), median_ttfv AS (
  SELECT AVG(time_to_first_value_days) AS median_ttfv_days
  FROM ordered_ttfv
  WHERE row_number IN ((total_rows + 1) / 2, (total_rows + 2) / 2)
), run_rate AS (
  SELECT SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS integration_success_rate
  FROM fact_integration_run
)
SELECT SUM(CASE WHEN project_status = 'Active' THEN 1 ELSE 0 END) AS active_implementations,
       ROUND((SELECT SUM(CASE WHEN actual_go_live_date <= committed_go_live_date THEN 1 ELSE 0 END) * 1.0 / COUNT(*) FROM completed), 6) AS on_time_go_live_rate,
       ROUND((SELECT median_ttfv_days FROM median_ttfv), 2) AS median_ttfv_days,
       SUM(CASE WHEN project_status = 'Active' AND risk_status IN ('Red','Amber') THEN 1 ELSE 0 END) AS at_risk_active_accounts,
       ROUND((SELECT integration_success_rate FROM run_rate), 6) AS integration_success_rate
FROM dim_account;
""".strip()
    sql_funnel = """
SELECT milestone, MIN(stage_order) AS stage_order,
       SUM(CASE WHEN actual_date <> '' THEN 1 ELSE 0 END) AS completed_accounts
FROM fact_milestone GROUP BY milestone ORDER BY stage_order;
""".strip()
    sql_connector = """
SELECT connector_id,
       ROUND(SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 6) AS success_rate,
       ROUND(SUM(records_accepted) * 1.0 / SUM(records_received), 6) AS data_acceptance_rate,
       ROUND(AVG(latency_ms), 0) AS average_latency_ms,
       SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) AS failed_runs
FROM fact_integration_run GROUP BY connector_id ORDER BY success_rate ASC;
""".strip()
    sql_cohort = """
SELECT substr(kickoff_date, 1, 7) AS kickoff_month,
       ROUND(AVG(julianday(actual_go_live_date) - julianday(kickoff_date)), 2) AS average_lead_days,
       COUNT(*) AS completed_accounts
FROM dim_account WHERE project_status = 'Completed'
GROUP BY kickoff_month ORDER BY kickoff_month;
""".strip()
    sql_risk = """
SELECT account_id,
       account_id || ' | ' || UPPER(risk_status) || ' | '
         || printf('%+d days', days_to_committed_go_live) AS account_risk_label,
       CASE risk_status WHEN 'Red' THEN 1 WHEN 'Amber' THEN 2 ELSE 3 END AS risk_order,
       fictional_account_name, segment, days_to_committed_go_live,
       readiness_rate, mapping_coverage, uat_pass_rate,
       recent_integration_success_rate, risk_status, risk_reason, next_action
FROM dim_account WHERE project_status = 'Active'
ORDER BY risk_order, days_to_committed_go_live ASC, account_id ASC;
""".strip()
    sql_errors = """
SELECT CASE WHEN error_code = '' THEN 'NONE' ELSE error_code END AS error_code,
       COUNT(*) AS runs,
       SUM(records_rejected) AS rejected_records
FROM fact_integration_run WHERE status = 'FAILED'
GROUP BY error_code ORDER BY runs DESC;
""".strip()
    summary = query_rows(con, sql_summary)
    funnel = query_rows(con, sql_funnel)
    connector_reliability = query_rows(con, sql_connector)
    cohort_lead = query_rows(con, sql_cohort)
    risk_queue = query_rows(con, sql_risk)
    error_pareto = query_rows(con, sql_errors)
    con.close()
    datasets = {
        "summary": summary, "funnel": funnel, "connector_reliability": connector_reliability,
        "cohort_lead": cohort_lead, "risk_queue": risk_queue, "error_pareto": error_pareto,
    }
    for name, rows in datasets.items():
        if rows:
            write_csv(project_dir / f"data/curated/{name}.csv", list(rows[0]), rows)
    write_json(project_dir / "data/curated/dashboard-data.json", datasets)
    write_json(project_dir / "data/curated/summary.json", summary[0])
    sql_all = "\n\n".join([
        "-- Portfolio KPIs\n" + sql_summary,
        "-- Implementation funnel\n" + sql_funnel,
        "-- Connector reliability\n" + sql_connector,
        "-- Cohort lead time\n" + sql_cohort,
        "-- Intervention queue\n" + sql_risk,
        "-- Error Pareto\n" + sql_errors,
    ])
    write_text(project_dir / "sql/analytics.sql", sql_all)
    write_text(project_dir / "sql/tests.sql", """
-- Every assertion should return zero rows.
SELECT run_id, COUNT(*) FROM fact_integration_run GROUP BY run_id HAVING COUNT(*) <> 1;
SELECT * FROM fact_integration_run WHERE records_accepted + records_rejected <> records_received;
SELECT * FROM fact_integration_run WHERE status = 'SUCCESS' AND error_code <> '';
SELECT * FROM dim_account WHERE actual_go_live_date <> '' AND actual_go_live_date < kickoff_date;

SELECT a.account_id
FROM dim_account a JOIN fact_milestone m USING (account_id)
WHERE m.milestone = 'First value' AND a.first_value_date <> m.actual_date;

SELECT account_id FROM dim_account
WHERE project_status = 'Active'
  AND risk_status <> CASE
    WHEN days_to_committed_go_live <= 14
         AND (mapping_coverage < 0.95 OR uat_pass_rate < 0.90) THEN 'Red'
    WHEN mapping_coverage < 0.95 OR uat_pass_rate < 0.90
         OR recent_integration_success_rate < 0.98
         OR days_to_committed_go_live < 22 THEN 'Amber'
    ELSE 'Green' END;
""")
    current = summary[0]
    top_risk = risk_queue[0] if risk_queue else None
    notebook = execute_notebook(project_dir, [
        ("markdown", f"""# SaaS Implementation & Integration Health\n\n## tl;dr\n\nThe synthetic portfolio has **{current['active_implementations']} active implementations**, **{current['at_risk_active_accounts']} red/amber accounts**, an on-time completed go-live rate of **{current['on_time_go_live_rate']:.1%}**, and median time to first value of **{current['median_ttfv_days']:.0f} days**. The first intervention account is **{top_risk['account_id'] if top_risk else 'none'}**.\n"""),
        ("markdown", """## Context & Methods\n\nDecision: which implementations risk missing committed go-live and what should happen next? Risk is rule-based, not an opaque score.\n\n### Key Assumptions\n\n- Completed and active projects use different eligibility rules.\n- Time to first value requires sync success, data acceptance, user adoption and a completed workflow.\n- Later template cohorts are observational synthetic comparisons, not causal evidence.\n"""),
        ("code", """from pathlib import Path\nimport csv, json\nPROJECT_DIR = Path.cwd()\ndef read_csv(name):\n    with (PROJECT_DIR / name).open(encoding='utf-8') as handle:\n        return list(csv.DictReader(handle))\nsummary = json.loads((PROJECT_DIR / 'data/curated/summary.json').read_text())\nrisk = read_csv('data/curated/risk_queue.csv')\nprint(json.dumps(summary, indent=2))\nprint(f\"active accounts in intervention view={len(risk)}\")\n"""),
        ("markdown", """## Data\n\nAccount, connector, milestone, mapping, UAT, sync-run, blocker and usage tables form a complete synthetic implementation lifecycle.\n"""),
        ("code", """runs = read_csv('data/raw/integration_runs.csv')\nreceived = sum(int(row['records_received']) for row in runs)\naccepted = sum(int(row['records_accepted']) for row in runs)\nsuccess = sum(row['status'] == 'SUCCESS' for row in runs)\nprint(f\"runs={len(runs):,} | success={success/len(runs):.2%} | data acceptance={accepted/received:.2%}\")\n"""),
        ("markdown", """## Results\n\nThe intervention queue ranks active accounts by explicit red/amber rules and committed date. Each row carries the reason and next action.\n"""),
        ("code", """for row in risk:\n    print(f\"{row['account_id']} | {row['risk_status']:<5} | days={row['days_to_committed_go_live']:>3} | mapping={float(row['mapping_coverage']):.0%} | UAT={float(row['uat_pass_rate']):.0%} | {row['next_action']}\")\n"""),
        ("markdown", """## Takeaways\n\n1. Act first on near-term red accounts with incomplete mapping or UAT.\n2. Connector reliability and data acceptance must be reviewed together; a successful HTTP response does not prove usable data.\n3. Treat cohort improvements as a process signal that needs controlled follow-up, not proof of causality.\n"""),
    ])
    write_json(project_dir / "notebooks/analysis.ipynb", notebook)

    definitions = [
        "On-Time Go-Live = completed implementations delivered on or before committed date / completed implementations.",
        "Median Time to First Value = median days from kickoff to first date meeting sync, acceptance, usage and workflow conditions.",
        "Integration Success = successful runs / all attempted non-cancelled runs.",
        "Data Acceptance = SUM(accepted records) / SUM(received records).",
        "Mapping Coverage = mapped required target fields / all required target fields.",
        "Required UAT Pass Rate = passed required cases / all required cases; not executed remains incomplete.",
        "Red risk = go-live within 14 days with mapping <95% or UAT <90%; amber covers incomplete mapping/UAT outside the red window, integration success <98%, or go-live within 22 days.",
    ]
    source_specs = []
    for source_id, label, sql, tables in [
        (
            "int_summary",
            "Implementation portfolio KPIs",
            sql_summary,
            ["dim_account", "fact_integration_run"],
        ),
        ("int_funnel", "Implementation funnel", sql_funnel, ["fact_milestone"]),
        ("int_connector", "Connector reliability", sql_connector, ["fact_integration_run"]),
        ("int_cohort", "Cohort lead time", sql_cohort, ["dim_account"]),
        ("int_risk", "Intervention queue", sql_risk, ["dim_account"]),
        ("int_errors", "Integration errors", sql_errors, ["fact_integration_run"]),
    ]:
        source_specs.append(artifact_source(
            source_id, label, sql, tables,
            definitions, "sql/analytics.sql", ["Synthetic accounts", "Snapshot through 2026-06-30"],
        ))
    cards = [
        make_card("active", "summary", "int_summary", "Active implementations", "active_implementations", "number", "Projects not complete at the snapshot date."),
        make_card("ontime", "summary", "int_summary", "On-time go-live", "on_time_go_live_rate", "percent", "Completed implementations delivered by committed date."),
        make_card("ttfv", "summary", "int_summary", "Median TTFV days", "median_ttfv_days", "number", "Median kickoff-to-first-value days for eligible accounts."),
        make_card("risk", "summary", "int_summary", "At-risk active", "at_risk_active_accounts", "number", "Active accounts classified red or amber by explicit rules."),
        make_card("success", "summary", "int_summary", "Integration success", "integration_success_rate", "percent", "Successful sync runs divided by all attempted runs."),
    ]
    charts = [
        make_chart("cohort", "Average implementation lead time by kickoff cohort", "line", "cohort_lead", "int_cohort", "kickoff_month", "average_lead_days", subtitle="Completed accounts only; observational synthetic cohorts", fmt="number", layout="full"),
        make_chart(
            "risk_matrix",
            "Active implementation readiness by account",
            "horizontalBar",
            "risk_queue",
            "int_risk",
            "account_risk_label",
            "readiness_rate",
            subtitle="Account | risk | days to committed go-live · critical-first order",
            fmt="percent",
            color="risk_status",
            layout="full",
        ),
        make_chart("errors", "Failed sync runs by error code", "horizontalBar", "error_pareto", "int_errors", "error_code", "runs", subtitle="Explicit synthetic OAuth, schema, rate-limit and upstream scenarios", fmt="number", layout="full"),
    ]
    tables = [
        {
            "id": "funnel_table", "title": "Implementation stage completion",
            "subtitle": "Count of 60 synthetic accounts with completed milestone",
            "dataset": "funnel", "sourceId": "int_funnel", "layout": "full", "density": "dense",
            "defaultSort": {"field": "stage_order", "direction": "asc"},
            "columns": [
                {"field": "stage_order", "label": "Stage", "format": "number"},
                {"field": "milestone", "label": "Milestone", "type": "text"},
                {"field": "completed_accounts", "label": "Completed accounts", "format": "number"},
            ],
        },
        {
            "id": "risk_table", "title": "Intervention queue", "subtitle": "Explicit reason, owner-level action and readiness evidence",
            "dataset": "risk_queue", "sourceId": "int_risk", "layout": "full", "density": "dense",
            "defaultSort": {"field": "days_to_committed_go_live", "direction": "asc"},
            "columns": [
                {"field": "account_id", "label": "Account", "type": "text"},
                {"field": "fictional_account_name", "label": "Fictional name", "type": "text"},
                {"field": "segment", "label": "Segment", "type": "text"},
                {"field": "risk_status", "label": "Risk", "type": "text"},
                {"field": "days_to_committed_go_live", "label": "Days to committed", "format": "number"},
                {"field": "readiness_rate", "label": "Readiness", "format": "percent"},
                {"field": "mapping_coverage", "label": "Mapping", "format": "percent"},
                {"field": "uat_pass_rate", "label": "Required UAT", "format": "percent"},
                {"field": "recent_integration_success_rate", "label": "7-day sync success", "format": "percent"},
                {"field": "next_action", "label": "Next action", "type": "text"},
            ],
        },
        {
            "id": "connector_table", "title": "Connector evidence", "dataset": "connector_reliability",
            "sourceId": "int_connector", "layout": "full", "density": "dense",
            "defaultSort": {"field": "success_rate", "direction": "asc"},
            "columns": [
                {"field": "connector_id", "label": "Connector", "type": "text"},
                {"field": "success_rate", "label": "Success", "format": "percent"},
                {"field": "data_acceptance_rate", "label": "Data acceptance", "format": "percent"},
                {"field": "average_latency_ms", "label": "Avg latency ms", "format": "number"},
                {"field": "failed_runs", "label": "Failed runs", "format": "number"},
            ],
        },
    ]
    blocks = [
        {"id": "intro", "type": "markdown", "body": "# SaaS Implementation & Integration Health\n\n**Decision:** which implementations risk missing committed go-live, why, and what intervention should happen next?\n\n*Deterministic synthetic portfolio data · 60 fictional accounts · snapshot 30 Jun 2026.*"},
        {"id": "metrics", "type": "metric-strip", "cardIds": [item["id"] for item in cards]},
        {"id": "funnel", "type": "table", "tableId": "funnel_table", "layout": "full"},
        {"id": "cohort", "type": "chart", "chartId": "cohort", "layout": "full"},
        {"id": "risk_matrix", "type": "chart", "chartId": "risk_matrix", "layout": "full"},
        {"id": "risk_queue", "type": "table", "tableId": "risk_table", "layout": "full"},
        {"id": "errors", "type": "chart", "chartId": "errors", "layout": "full"},
        {"id": "connector_table", "type": "table", "tableId": "connector_table", "layout": "full"},
        {"id": "method", "type": "markdown", "body": "## Method and limitations\n\nRisk is determined by visible schedule, mapping, UAT and reliability rules—not an opaque health score. Readiness combines mapping (40%), required UAT (30%) and recent sync success (30%) for chart positioning; the red/amber intervention status still follows the explicit guardrails. Template-cohort comparisons are observational synthetic patterns and do not establish causality. Account names, payloads and outcomes are fictional."},
    ]
    artifact_manifest = {
        "version": 1, "surface": "dashboard", "title": "SaaS Implementation & Integration Health",
        "description": "Synthetic implementation portfolio, connector reliability and intervention dashboard.",
        "generatedAt": GENERATED_AT, "cards": cards, "charts": charts, "tables": tables, "blocks": blocks,
    }
    write_text(project_dir / "README.md", f"""
# SaaS Implementation & Integration Health

Technical implementation and data-integration portfolio project using deterministic synthetic data.

## Decision

Which implementations risk missing committed go-live, why, and what should happen next?

## Reproduce

```bash
python3 scripts/build_analytics_projects.py --project integration
python3 scripts/validate_portfolio_data.py --project integration
```

- Fictional accounts: {len(accounts)}
- Integration runs: {len(integration_runs):,}
- Seed: {seed}
- SQL: `sql/analytics.sql`
- Executed notebook: `notebooks/analysis.ipynb`
- API contract and implementation artifacts: `docs/`

No real customer, endpoint, token, employer workflow or confidential information is included.
""")
    write_text(project_dir / "docs/metric-dictionary.md", "# Metric dictionary\n\n" + "\n".join(f"- {item}" for item in definitions))
    write_text(project_dir / "docs/data-dictionary.md", """
# Data dictionary

- `accounts.csv`: one row per fictional implementation account.
- `account_connectors.csv`: account-to-connector configuration.
- `milestones.csv`: one row per account × lifecycle milestone.
- `mapping_validation.csv`: one row per required target field.
- `uat_results.csv`: one row per required test case.
- `integration_runs.csv`: one row per attempted production sync.
- `blockers.csv`: open intervention records.
- `usage_daily.csv`: post-live adoption evidence used for first value.
""")
    write_text(project_dir / "docs/openapi.yaml", """
openapi: 3.0.3
info:
  title: RelayMetrics Synthetic Ingestion API
  version: 1.0.0
  description: Fictional portfolio contract; no production endpoint exists.
paths:
  /v1/events:
    post:
      summary: Submit a bounded synthetic event batch
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [account_id, events]
              properties:
                account_id: {type: string}
                events:
                  type: array
                  maxItems: 1000
                  items:
                    type: object
                    required: [event_id, event_time, metric_name, metric_value]
      responses:
        '202': {description: Accepted for validation}
        '400': {description: Contract violation}
        '401': {description: Authentication failed}
        '429': {description: Rate limited}
""")
    write_json(project_dir / "docs/postman_collection.json", {
        "info": {"name": "RelayMetrics Synthetic Integration", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"},
        "item": [{
            "name": "Submit synthetic event batch",
            "request": {"method": "POST", "header": [{"key": "Authorization", "value": "Bearer {{synthetic_token}}"}],
                        "url": {"raw": "https://example.invalid/v1/events", "protocol": "https", "host": ["example", "invalid"], "path": ["v1", "events"]},
                        "body": {"mode": "raw", "raw": json.dumps({"account_id": "ACCT-001", "events": [{"event_id": "evt-001", "event_time": "2026-06-30T12:00:00Z", "metric_name": "active_users", "metric_value": 4}]}, indent=2)}},
        }],
    })
    write_text(project_dir / "docs/source-to-target-mapping.csv", """
source_field,target_field,type,required,validation
customer_id,account_id,string,yes,non-empty
timestamp,event_time,datetime,yes,ISO-8601 UTC
source_record_id,source_id,string,yes,unique within account
measure_name,metric_name,string,yes,accepted taxonomy
measure_value,metric_value,number,yes,finite numeric
currency,currency,string,no,ISO-4217 when monetary
""")
    write_text(project_dir / "docs/uat-plan.md", """
# UAT plan

1. Authentication and least-privilege access
2. Required-field mapping
3. Historical load reconciliation
4. Incremental sync and idempotency
5. Retry and rate-limit behavior
6. Timezone boundary handling
7. Dashboard metric reconciliation
8. Operational handoff and owner signoff

Go-live requires every required case to be executed and at least 90% to pass, with no unresolved high-severity defect.
""")
    write_text(project_dir / "docs/go-live-runbook.md", """
# Go-live and hypercare runbook

## Before go-live

- Confirm OAuth/API credentials and expiry ownership.
- Lock mapping and schema version.
- Reconcile a representative historical load.
- Complete required UAT and rollback decision.

## Hypercare

- Monitor 401/403 authentication failures.
- Apply bounded exponential backoff to 429 responses.
- Quarantine schema-drift records rather than silently dropping them.
- Reconcile received, accepted and rejected record counts.
- Confirm timezone and deduplication behavior at the daily boundary.
""")
    write_text(project_dir / "docs/raci.md", """
# RACI

| Activity | Implementation | Integration Eng | Customer owner | Analytics owner |
|---|---|---|---|---|
| Discovery | R | C | A | C |
| Authentication | C | R | A | I |
| Mapping | R | C | C | A |
| UAT | R | C | A | A |
| Go-live | R | R | A | C |
| Hypercare | A | R | C | C |
""")
    write_text(project_dir / "docs/qa-report.md", """
# QA report

The build and independent validator verify unique run IDs, timestamp order, `accepted + rejected = received`, status/error consistency, account/connector integrity, milestone order, activation eligibility, usage-derived first-value conditions, account-to-milestone first-value equality, risk-rule derivation and dashboard/SQL reconciliation.
""")
    receipt = build_artifact(project_dir, artifact_manifest, datasets, source_specs)
    manifest_for(project_dir, seed, "integration-v1")
    return {"project": "integration", "rows": len(integration_runs), "receipt": receipt, "summary": current}


PROJECT_MAP = {
    "commercial": ("projects/marketing-command-center", build_commercial),
    "reliability": ("projects/ga4-quality-monitor", build_reliability),
    "integration": ("projects/analytics-change-control", build_integration),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", choices=["all", *PROJECT_MAP], default="all")
    args = parser.parse_args()
    selected = PROJECT_MAP.items() if args.project == "all" else [(args.project, PROJECT_MAP[args.project])]
    results = []
    for name, (relative_path, builder) in selected:
        print(f"Building {name}...", flush=True)
        results.append(builder(ROOT / relative_path))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
