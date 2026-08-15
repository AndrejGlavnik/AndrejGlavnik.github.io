#!/usr/bin/env python3
"""Independently validate the three synthetic analytics portfolio projects."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = {
    "commercial": ROOT / "projects/marketing-command-center",
    "reliability": ROOT / "projects/ga4-quality-monitor",
    "integration": ROOT / "projects/analytics-change-control",
}


class Validation:
    def __init__(self, name):
        self.name = name
        self.checks = []
        self.failures = []

    def check(self, condition, label, evidence=""):
        item = {"check": label, "status": "PASS" if condition else "FAIL"}
        if evidence != "":
            item["evidence"] = evidence
        self.checks.append(item)
        if not condition:
            self.failures.append(item)

    def close(self):
        return {
            "project": self.name,
            "status": "PASS" if not self.failures else "FAIL",
            "check_count": len(self.checks),
            "failure_count": len(self.failures),
            "checks": self.checks,
        }


def read_csv(path):
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def close(left, right, tolerance=1e-6):
    return abs(float(left) - float(right)) <= tolerance


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def base_tables(sql):
    ctes = {
        match.group(1).lower()
        for match in re.finditer(
            r"(?:\bWITH|,)\s*([A-Za-z_][A-Za-z0-9_]*)\s+AS\s*\(",
            sql,
            flags=re.IGNORECASE,
        )
    }
    referenced = {
        match.group(1).lower()
        for match in re.finditer(
            r"\b(?:FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_]*)",
            sql,
            flags=re.IGNORECASE,
        )
    }
    return referenced - ctes


def artifact_fields(item):
    fields = []
    for metric in item.get("metrics", []):
        fields.append(metric.get("field"))
    encodings = item.get("encodings", {})
    for encoding in encodings.values():
        fields.extend(encoding.get("fields", []))
        if encoding.get("field"):
            fields.append(encoding["field"])
    for column in item.get("columns", []):
        fields.append(column.get("field"))
    return [field for field in fields if field]


def validate_common(name, project, validation):
    required = [
        "index.html", "artifact.json", "README.md", "data/build-manifest.json",
        "data/portable-build-receipt.json", "data/curated/dashboard-data.json",
        "sql/analytics.sql", "sql/tests.sql", "notebooks/analysis.ipynb",
        "docs/metric-dictionary.md", "docs/data-dictionary.md", "docs/qa-report.md",
    ]
    for relative in required:
        validation.check((project / relative).is_file(), f"Required artifact exists: {relative}")
    if validation.failures:
        return
    receipt = read_json(project / "data/portable-build-receipt.json")
    validation.check(receipt.get("ok") is True, "Canonical portable build succeeded")
    validation.check(receipt.get("stages") == {"validation": "passed", "package": "passed", "verification": "passed"},
                     "Artifact validation, packaging and browser verification passed", receipt.get("stages"))
    validation.check(receipt.get("viewports") == [1440, 390], "Desktop and narrow viewports verified", receipt.get("viewports"))
    validation.check(receipt.get("sourceDialog") == "passed", "Source dialog verified")
    receipt_html = receipt.get("html", "")
    validation.check(
        bool(receipt_html)
        and not Path(receipt_html).is_absolute()
        and ".." not in Path(receipt_html).parts,
        "Portable receipt exposes only a repository-relative HTML path",
        receipt_html,
    )
    validation.check(
        (ROOT / receipt_html).resolve() == (project / "index.html").resolve()
        if receipt_html else False,
        "Portable receipt resolves to this project's delivered index",
    )
    html = (project / "index.html").read_text(encoding="utf-8")
    validation.check("data-analytics-portable-reader" in html and "data-analytics-portable-fallback" in html,
                     "Self-contained enhanced and semantic readers are embedded")
    validation.check("<script src=" not in html.lower(), "No external script dependency")
    artifact = read_json(project / "artifact.json")
    validation.check(artifact.get("surface") == "dashboard", "Canonical dashboard surface declared")
    validation.check(
        artifact.get("manifest", {}).get("surface") == artifact.get("surface"),
        "Manifest and artifact surfaces agree",
    )
    validation.check(artifact.get("snapshot", {}).get("status") == "fixture", "Synthetic snapshot is labeled fixture")
    validation.check(
        artifact.get("manifest", {}).get("generatedAt")
        == artifact.get("snapshot", {}).get("generatedAt"),
        "Manifest and snapshot timestamps agree",
    )
    validation.check(
        artifact.get("sources") == artifact.get("manifest", {}).get("sources"),
        "Top-level and manifest source inventories agree",
    )
    source_ids = {source.get("id") for source in artifact["manifest"].get("sources", [])}
    referenced = []
    for collection in ("cards", "charts", "tables"):
        for item in artifact["manifest"].get(collection, []):
            if item.get("sourceId"):
                referenced.append(item["sourceId"])
    validation.check(all(source_id in source_ids for source_id in referenced),
                     "Every card, chart and table resolves canonical provenance")
    validation.check(all(source.get("path") and ".." not in source["path"] for source in artifact["manifest"].get("sources", [])),
                     "Source paths are repository-relative and safe")
    source_paths_resolve = True
    source_sql_matches = True
    source_tables_match = True
    for source in artifact["manifest"].get("sources", []):
        source_path = project / source.get("path", "")
        query = source.get("query", {})
        if not source_path.is_file():
            source_paths_resolve = False
            source_text = ""
        else:
            source_text = source_path.read_text(encoding="utf-8")
        if not query.get("sql") or query.get("sql") not in source_text:
            source_sql_matches = False
        if base_tables(query.get("sql", "")) != {
            table.lower() for table in query.get("tables_used", [])
        }:
            source_tables_match = False
    validation.check(source_paths_resolve, "Every canonical source path exists")
    validation.check(source_sql_matches, "Every exposed query exactly matches the repository SQL")
    validation.check(source_tables_match, "Every source declares the exact base tables used by its query")
    datasets = artifact.get("snapshot", {}).get("datasets", {})
    dataset_fields_valid = True
    for collection in ("cards", "charts", "tables"):
        for item in artifact["manifest"].get(collection, []):
            rows = datasets.get(item.get("dataset"))
            if not rows:
                dataset_fields_valid = False
                continue
            available = set(rows[0])
            if any(field not in available for field in artifact_fields(item)):
                dataset_fields_valid = False
    validation.check(dataset_fields_valid, "Every card, chart and table field exists in its dataset")
    card_ids = {item["id"] for item in artifact["manifest"].get("cards", [])}
    chart_ids = {item["id"] for item in artifact["manifest"].get("charts", [])}
    table_ids = {item["id"] for item in artifact["manifest"].get("tables", [])}
    block_refs_resolve = True
    for block in artifact["manifest"].get("blocks", []):
        if block.get("type") == "metric-strip":
            block_refs_resolve &= set(block.get("cardIds", [])) <= card_ids
        elif block.get("type") == "chart":
            block_refs_resolve &= block.get("chartId") in chart_ids
        elif block.get("type") == "table":
            block_refs_resolve &= block.get("tableId") in table_ids
    validation.check(block_refs_resolve, "Every manifest block resolves its card, chart or table")
    notebook = read_json(project / "notebooks/analysis.ipynb")
    code_cells = [cell for cell in notebook.get("cells", []) if cell.get("cell_type") == "code"]
    validation.check(notebook.get("nbformat") == 4, "Notebook uses nbformat 4")
    validation.check(bool(code_cells), "Notebook includes executable analysis cells")
    validation.check(all(cell.get("execution_count") for cell in code_cells), "Every notebook code cell was executed")
    validation.check(all(not any(output.get("output_type") == "error" for output in cell.get("outputs", [])) for cell in code_cells),
                     "Executed notebook contains no error output")
    notebook_text = "".join("".join(cell.get("source", [])) for cell in notebook.get("cells", []))
    for section in ("## tl;dr", "## Context & Methods", "## Data", "## Results", "## Takeaways"):
        validation.check(section in notebook_text, f"Notebook contains {section}")
    manifest = read_json(project / "data/build-manifest.json")
    manifest_entries = {row["path"]: row for row in manifest.get("files", [])}
    validation.check(manifest.get("synthetic") is True, "Build manifest labels data synthetic")
    actual_manifest_paths = {
        path.relative_to(project).as_posix()
        for path in project.rglob("*")
        if path.is_file()
        and path.name
        not in {"build-manifest.json", "index.html", "portable-build-receipt.json"}
    }
    validation.check(
        set(manifest_entries) == actual_manifest_paths,
        "Build manifest covers every deterministic project file exactly once",
        {
            "listed": len(manifest_entries),
            "actual": len(actual_manifest_paths),
        },
    )
    hash_matches = True
    for relative, metadata in manifest_entries.items():
        path = project / relative
        if not path.exists() or sha256(path) != metadata["sha256"] or path.stat().st_size != metadata["bytes"]:
            hash_matches = False
            break
    validation.check(hash_matches, "Build manifest hashes and byte counts reconcile")
    public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in project.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".md", ".json", ".sql", ".yaml", ".csv", ".html"}
    ).lower()
    validation.check(
        "/users/" not in public_text and "file://" not in public_text,
        "Public project artifacts contain no absolute workstation path",
    )
    validation.check(
        not any(term in public_text for term in ("danone", "databox", "saatchi")),
        "Synthetic project artifacts contain no employer or client identifiers",
    )


def validate_commercial(project):
    v = Validation("commercial")
    validate_common("commercial", project, v)
    if v.failures:
        return v.close()
    sales = read_csv(project / "data/raw/sales_daily.csv")
    budgets = read_csv(project / "data/raw/budget_forecast.csv")
    promotions = read_csv(project / "data/raw/promotions.csv")
    artifact = read_json(project / "artifact.json")
    summary = artifact["snapshot"]["datasets"]["summary"][0]
    grain = [(row["date"], row["sku_id"], row["market"], row["channel"]) for row in sales]
    v.check(len(grain) == len(set(grain)), "Daily sales composite grain is unique", f"rows={len(grain):,}")
    formula_errors = 0
    return_errors = 0
    net_revenue = gross_profit = 0.0
    net_units = 0
    actual_by_slice = defaultdict(int)
    for row in sales:
        gross_units = int(row["gross_units"])
        returns = int(row["return_units"])
        units = int(row["net_units"])
        expected_revenue = float(row["gross_revenue_eur"]) - float(row["return_value_eur"]) - float(row["discount_value_eur"])
        if returns > gross_units or units != gross_units - returns:
            return_errors += 1
        if abs(float(row["net_revenue_eur"]) - expected_revenue) > 0.011:
            formula_errors += 1
        net_revenue += float(row["net_revenue_eur"])
        gross_profit += float(row["gross_profit_eur"])
        net_units += units
        actual_by_slice[(row["month"], row["sku_id"], row["market"], row["channel"])] += units
    v.check(return_errors == 0, "Returns and net-unit formulas are valid", f"violations={return_errors}")
    v.check(formula_errors == 0, "Net-revenue row formulas reconcile to €0.01", f"violations={formula_errors}")
    budget_keys = {(row["month"], row["sku_id"], row["market"], row["channel"]) for row in budgets}
    v.check(set(actual_by_slice) == budget_keys, "Every actual slice has one budget/forecast slice", f"slices={len(budget_keys):,}")
    v.check(
        len(budget_keys) == len(budgets),
        "Monthly budget/forecast composite grain is unique",
        f"rows={len(budgets):,}",
    )
    invalid_lock_dates = sum(
        row.get("forecast_locked_at", "") >= f"{row['month']}-01"
        for row in budgets
    )
    v.check(
        invalid_lock_dates == 0,
        "Every forecast was locked before its reporting month",
        f"violations={invalid_lock_dates}",
    )
    v.check(
        all(
            row.get("forecast_method")
            == "calendar_plan_v1_no_realized_demand"
            for row in budgets
        ),
        "Forecast explicitly excludes realized daily demand",
    )
    basis_bounds = sum(
        not (
            max(1, round(int(row["forecast_basis_units"]) * 0.92)) - 31
            <= int(row["forecast_units"])
            <= round(int(row["forecast_basis_units"]) * 1.08) + 31
        )
        for row in budgets
    )
    v.check(
        basis_bounds == 0,
        "Locked forecasts stay within the documented ex-ante planning band",
        f"violations={basis_bounds}",
    )
    forecast_basis_by_slice = {
        (row["month"], row["sku_id"], row["market"], row["channel"]):
        int(row["forecast_basis_units"])
        for row in budgets
    }
    actual_basis_matches = sum(
        actual_by_slice[key] == forecast_basis_by_slice[key]
        for key in actual_by_slice
    )
    v.check(
        actual_basis_matches / len(actual_by_slice) < 0.50,
        "Forecast basis is not a copy of realized actual units",
        f"exact_match_rate={actual_basis_matches / len(actual_by_slice):.2%}",
    )
    budget_revenue = sum(float(row["budget_revenue_eur"]) for row in budgets)
    forecast_by_slice = {(row["month"], row["sku_id"], row["market"], row["channel"]): int(row["forecast_units"]) for row in budgets}
    forecast_wape = sum(abs(actual_by_slice[key] - forecast_by_slice[key]) for key in actual_by_slice) / net_units
    expected = {
        "net_revenue": round(net_revenue, 2),
        "budget_variance_rate": round((net_revenue - budget_revenue) / budget_revenue, 6),
        "gross_margin_rate": round(gross_profit / net_revenue, 6),
        "net_units": net_units,
        "forecast_wape": round(forecast_wape, 6),
    }
    for field, value in expected.items():
        tolerance = 0.011 if field == "net_revenue" else 1e-6
        v.check(close(summary[field], value, tolerance), f"Summary KPI reconciles: {field}", {"artifact": summary[field], "raw": value})
    promo_errors = 0
    for row in promotions:
        investment = float(row["promotion_investment_eur"])
        expected_roi = float(row["incremental_profit_eur"]) / investment if investment else 0
        if abs(float(row["promotion_roi"]) - expected_roi) > 1.1e-6:
            promo_errors += 1
    v.check(promo_errors == 0, "Promotion ROI reconciles for every promotion", f"violations={promo_errors}")
    promo_discounts = {float(row["discount_pct"]) for row in promotions}
    v.check(
        promo_discounts == {0.10, 0.15, 0.20, 0.30},
        "All four planned promotion discount bands are represented",
        sorted(promo_discounts),
    )
    mechanics_by_band = defaultdict(set)
    expected_execution_lift = {
        "Feature": 0.25,
        "Display": 0.35,
        "Bundle": 0.22,
        "Price cut": 0.08,
    }
    invalid_lift_assumptions = 0
    for row in promotions:
        mechanics_by_band[float(row["discount_pct"])].add(row["mechanic"])
        if not close(
            row.get("execution_lift_pct", -1),
            expected_execution_lift.get(row["mechanic"], -2),
        ):
            invalid_lift_assumptions += 1
    v.check(
        all(
            mechanics_by_band[band] == set(expected_execution_lift)
            for band in {0.10, 0.15, 0.20, 0.30}
        ),
        "Every discount band spans all four execution mechanics",
        {str(band): sorted(mechanics_by_band[band]) for band in sorted(mechanics_by_band)},
    )
    v.check(
        invalid_lift_assumptions == 0,
        "Every promotion carries its disclosed execution-lift assumption",
        f"violations={invalid_lift_assumptions}",
    )
    promo_rows = artifact["snapshot"]["datasets"]["promo_performance"]
    v.check(
        len(promo_rows) == 4,
        "Promotion decision view has one weighted row per discount band",
        f"rows={len(promo_rows)}",
    )
    v.check(
        any(float(row["promotion_roi"]) > 0 for row in promo_rows)
        and any(float(row["promotion_roi"]) <= 0 for row in promo_rows),
        "Promotion scenarios contain a realistic mix of value-creating and value-destructive bands",
    )
    promo_sql = (project / "sql/analytics.sql").read_text(encoding="utf-8")
    v.check(
        "SUM(incremental_profit_eur) / SUM(promotion_investment_eur)"
        in promo_sql,
        "Promotion ROI is a ratio of sums, not an average of averages",
    )
    decision_blocks = [
        block for block in artifact["manifest"].get("blocks", [])
        if block.get("id") == "promotion_decision"
    ]
    v.check(
        len(decision_blocks) == 1
        and decision_blocks[0].get("sourceId") == "commercial_promo"
        and "Recommendation:" in decision_blocks[0].get("body", ""),
        "Promotion recommendation is visible and source-backed",
    )
    monthly = artifact["snapshot"]["datasets"]["monthly"]
    v.check(close(sum(float(row["actual_revenue"]) for row in monthly), summary["net_revenue"], 0.02),
            "Monthly chart totals reconcile with hero revenue")
    v.check("modeled" in (project / "docs/methodology.md").read_text(encoding="utf-8").lower(),
            "Promotion baseline limitation is documented")
    v.check(
        all(row["status"] == "PASS" for row in read_csv(project / "data/curated/quality_checks.csv")),
        "Generated commercial QA evidence contains no hard-coded false pass",
    )
    return v.close()


def validate_reliability(project):
    v = Validation("reliability")
    validate_common("reliability", project, v)
    if v.failures:
        return v.close()
    quality = read_csv(project / "data/raw/quality_results.csv")
    runs = read_csv(project / "data/raw/pipeline_runs.csv")
    releases = read_csv(project / "data/raw/releases.csv")
    changes = read_csv(project / "data/raw/change_requests.csv")
    incidents = read_csv(project / "data/raw/incidents.csv")
    artifact = read_json(project / "artifact.json")
    summary = artifact["snapshot"]["datasets"]["summary"][0]
    result_keys = [(row["run_id"], row["rule_id"]) for row in quality]
    v.check(len(result_keys) == len(set(result_keys)), "One quality result per run × rule", f"results={len(result_keys):,}")
    status_errors = 0
    for row in quality:
        observed, threshold = float(row["observed_value"]), float(row["threshold"])
        passed = observed <= threshold if row["operator"] == "<=" else observed >= threshold
        expected_status = "PASS" if passed else ("FAIL" if row["severity"] == "Critical" else "WARN")
        if row["status"] != expected_status:
            status_errors += 1
    v.check(status_errors == 0, "Every test status follows operator, threshold and severity", f"violations={status_errors}")
    by_key = {(row["run_date"], row["asset_id"], row["rule_id"]): row for row in quality}
    expected_anomalies = [
        (("2026-04-14", "WEB_EVENTS", "DQ-UNIQUE"), "FAIL"),
        (("2026-04-15", "WEB_EVENTS", "DQ-RECON"), "FAIL"),
        (("2026-05-08", "CAMPAIGN_SPEND", "DQ-TAXONOMY"), "WARN"),
        (("2026-06-03", "CRM_LEADS", "DQ-COMPLETE"), "FAIL"),
        (("2026-06-03", "CRM_LEADS", "DQ-FRESH"), "WARN"),
        (("2026-06-17", "COMMERCE_ORDERS", "DQ-VALID"), "WARN"),
        (("2026-06-30", "CAMPAIGN_SPEND", "DQ-TAXONOMY"), "WARN"),
    ]
    for key, status in expected_anomalies:
        v.check(by_key.get(key, {}).get("status") == status, f"Injected scenario detected: {' / '.join(key)}")
    recent_quality = [row for row in quality if row["run_date"] >= "2026-06-01"]
    critical = [row for row in recent_quality if row["severity"] == "Critical"]
    critical_pass = sum(row["status"] == "PASS" for row in critical) / len(critical)
    recent_runs = [row for row in runs if row["run_date"] >= "2026-06-01"]
    freshness = sum(int(row["freshness_minutes"]) <= 240 and row["pipeline_status"] == "SUCCEEDED" for row in recent_runs) / len(recent_runs)
    run_lookup = {row["run_id"]: row for row in runs}
    recon_errors = 0
    for row in quality:
        if row["rule_id"] != "DQ-RECON":
            continue
        run = run_lookup[row["run_id"]]
        governed = float(run["governed_value"])
        dashboard = float(run["dashboard_value"])
        expected_recon = abs(dashboard - governed) / abs(governed)
        if abs(float(row["observed_value"]) - expected_recon) > 1.1e-6:
            recon_errors += 1
    v.check(
        recon_errors == 0,
        "Every reconciliation result recomputes from governed and dashboard raw inputs",
        f"violations={recon_errors}",
    )
    latest_recon = max(
        abs(float(row["dashboard_value"]) - float(row["governed_value"]))
        / abs(float(row["governed_value"]))
        for row in runs if row["run_date"] == "2026-06-30"
    )
    open_incidents = sum(
        row["resolved_at"] == "" and row["severity"] in ("High", "Critical")
        for row in incidents
    )
    lead_days = []
    for row in changes:
        if row["release_date"] <= "2026-06-30":
            from datetime import date
            lead_days.append((date.fromisoformat(row["release_date"]) - date.fromisoformat(row["ready_date"])).days)
    latest_release = max(releases, key=lambda row: row["scheduled_date"])
    release_lineage_errors = 0
    for release in releases:
        evidence = [
            row for row in quality
            if row["run_date"] == release["evidence_date"]
        ]
        critical_failures = sum(
            row["severity"] == "Critical" and row["status"] == "FAIL"
            for row in evidence
        )
        high_warnings = sum(
            row["severity"] == "High" and row["status"] == "WARN"
            for row in evidence
        )
        if (
            int(release["critical_failures"]) != critical_failures
            or int(release["high_warnings"]) != high_warnings
        ):
            release_lineage_errors += 1
    v.check(
        release_lineage_errors == 0,
        "Every release failure/warning count derives from its recorded evidence date",
        f"violations={release_lineage_errors}",
    )
    accepted = [row for row in releases if int(row["exceptions_accepted"])]
    exception_errors = sum(
        not row["exception_owner"]
        or not row["exception_expiry"]
        or row["exception_expiry"] <= row["scheduled_date"]
        or not row["exception_reason"]
        for row in accepted
    )
    v.check(
        bool(accepted) and exception_errors == 0,
        "Every accepted caveat has a reason, owner and future expiry",
        f"accepted={len(accepted)}; violations={exception_errors}",
    )
    if int(latest_release["critical_failures"]) > 0 or not int(latest_release["signoff_complete"]) or not int(latest_release["rollback_ready"]):
        decision = "HOLD"
    elif (
        1 <= int(latest_release["high_warnings"]) <= 2
        and int(latest_release["exceptions_accepted"])
        and latest_release["exception_owner"]
        and latest_release["exception_expiry"] > latest_release["scheduled_date"]
    ):
        decision = "SHIP WITH CAVEAT"
    elif int(latest_release["high_warnings"]) == 0:
        decision = "SHIP"
    else:
        decision = "HOLD"
    expected = {
        "release_decision": decision,
        "critical_pass_rate": round(critical_pass, 6),
        "freshness_sla_rate": round(freshness, 6),
        "latest_reconciliation_variance": round(latest_recon, 6),
        "open_high_critical_incidents": open_incidents,
        "average_change_lead_days": round(sum(lead_days) / len(lead_days), 2),
    }
    for field, value in expected.items():
        condition = summary[field] == value if isinstance(value, str) else close(summary[field], value, 1e-6)
        v.check(condition, f"Summary KPI reconciles: {field}", {"artifact": summary[field], "raw": value})
    v.check(summary["release_decision"] == "SHIP WITH CAVEAT", "Candidate release demonstrates an accepted, owned caveat")
    scenario = read_json(project / "data/scenario-manifest.json")
    v.check(len(scenario.get("injected_scenarios", [])) == 5, "All five injected anomaly scenarios are disclosed")
    disclosed_dates = {
        (scenario_row["asset"], date)
        for scenario_row in scenario.get("injected_scenarios", [])
        for date in scenario_row.get("dates", [])
    }
    observed_scenario_dates = {
        (row["asset_id"], row["run_date"])
        for row in quality if row["status"] != "PASS"
    }
    v.check(
        observed_scenario_dates <= disclosed_dates,
        "Every non-pass asset/date is explicitly disclosed in the scenario manifest",
        f"observed={len(observed_scenario_dates)}; disclosed={len(disclosed_dates)}",
    )
    reconciliation_rows = artifact["snapshot"]["datasets"]["reconciliation"]
    reconciliation_chart = next(
        chart for chart in artifact["manifest"]["charts"]
        if chart["id"] == "latest_recon"
    )
    v.check(
        reconciliation_chart["type"] == "horizontalBar"
        and reconciliation_chart["encodings"]["y"]["field"] == "reconciliation_variance_bps"
        and reconciliation_chart["encodings"]["y"].get("format") == "number"
        and "Basis points" in reconciliation_chart.get("subtitle", ""),
        "Reconciliation chart uses an explicit basis-point scale with readable precision",
    )
    v.check(
        all(
            close(
                row["reconciliation_variance_bps"],
                float(row["reconciliation_variance"]) * 10000,
                0.011,
            )
            for row in reconciliation_rows
        ),
        "Every reconciliation basis-point value derives from the fractional variance",
    )
    return v.close()


def validate_integration(project):
    v = Validation("integration")
    validate_common("integration", project, v)
    if v.failures:
        return v.close()
    accounts = read_csv(project / "data/raw/accounts.csv")
    connectors = read_csv(project / "data/raw/account_connectors.csv")
    milestones = read_csv(project / "data/raw/milestones.csv")
    mappings = read_csv(project / "data/raw/mapping_validation.csv")
    uat_results = read_csv(project / "data/raw/uat_results.csv")
    runs = read_csv(project / "data/raw/integration_runs.csv")
    blockers = read_csv(project / "data/raw/blockers.csv")
    usage = read_csv(project / "data/raw/usage_daily.csv")
    artifact = read_json(project / "artifact.json")
    summary = artifact["snapshot"]["datasets"]["summary"][0]
    run_ids = [row["run_id"] for row in runs]
    v.check(len(run_ids) == len(set(run_ids)), "Integration run IDs are unique", f"runs={len(run_ids):,}")
    account_ids = {row["account_id"] for row in accounts}
    v.check(
        len(account_ids) == len(accounts),
        "Implementation account IDs are unique",
        f"accounts={len(accounts)}",
    )
    v.check(
        len(connectors)
        == len({(row["account_id"], row["connector_id"]) for row in connectors}),
        "Account × connector grain is unique",
        f"rows={len(connectors)}",
    )
    v.check(
        len(milestones)
        == len({(row["account_id"], row["milestone"]) for row in milestones}),
        "Account × milestone grain is unique",
        f"rows={len(milestones)}",
    )
    v.check(
        len(mappings)
        == len({(row["account_id"], row["connector_id"], row["target_field"]) for row in mappings}),
        "Account × connector × mapping-field grain is unique",
        f"rows={len(mappings)}",
    )
    v.check(
        len(uat_results)
        == len({(row["account_id"], row["uat_case_id"]) for row in uat_results}),
        "Account × required-UAT-case grain is unique",
        f"rows={len(uat_results)}",
    )
    child_rows = connectors + milestones + mappings + uat_results + runs + blockers + usage
    v.check(
        all(row["account_id"] in account_ids for row in child_rows),
        "Every implementation child row resolves an account",
    )
    connector_keys = {(row["account_id"], row["connector_id"]) for row in connectors}
    v.check(
        all((row["account_id"], row["connector_id"]) in connector_keys for row in runs),
        "Every integration run resolves an authorized account connector",
    )
    count_errors = sum(int(row["records_accepted"]) + int(row["records_rejected"]) != int(row["records_received"]) for row in runs)
    v.check(count_errors == 0, "Accepted + rejected records equal received records", f"violations={count_errors}")
    status_errors = sum((row["status"] == "SUCCESS" and row["error_code"] != "") or (row["status"] == "FAILED" and row["error_code"] == "") for row in runs)
    v.check(status_errors == 0, "Run status and error-code semantics agree", f"violations={status_errors}")
    error_codes = Counter(row["error_code"] for row in runs if row["error_code"])
    for code in ("OAUTH_TOKEN_EXPIRED", "SCHEMA_FIELD_CHANGED", "RATE_LIMITED"):
        v.check(error_codes[code] > 0, f"Injected integration scenario is observable: {code}", error_codes[code])
    active = [row for row in accounts if row["project_status"] == "Active"]
    completed = [row for row in accounts if row["project_status"] == "Completed"]
    on_time = sum(row["actual_go_live_date"] <= row["committed_go_live_date"] for row in completed) / len(completed)
    ttfv = sorted(int(row["time_to_first_value_days"]) for row in accounts if row["time_to_first_value_days"])
    median_ttfv = statistics.median(ttfv)
    at_risk = sum(row["risk_status"] in ("Red", "Amber") for row in active)
    success = sum(row["status"] == "SUCCESS" for row in runs) / len(runs)
    expected = {
        "active_implementations": len(active),
        "on_time_go_live_rate": round(on_time, 6),
        "median_ttfv_days": round(median_ttfv, 2),
        "at_risk_active_accounts": at_risk,
        "integration_success_rate": round(success, 6),
    }
    for field, value in expected.items():
        v.check(close(summary[field], value, 1e-6), f"Summary KPI reconciles: {field}", {"artifact": summary[field], "raw": value})
    risk_errors = 0
    for row in active:
        days = int(row["days_to_committed_go_live"])
        mapping = float(row["mapping_coverage"])
        uat = float(row["uat_pass_rate"])
        reliability = float(row["recent_integration_success_rate"])
        if days <= 14 and (mapping < 0.95 or uat < 0.90):
            expected_risk = "Red"
        elif mapping < 0.95 or uat < 0.90 or reliability < 0.98 or days < 22:
            expected_risk = "Amber"
        else:
            expected_risk = "Green"
        if row["risk_status"] != expected_risk:
            risk_errors += 1
    v.check(risk_errors == 0, "Every active risk status follows the documented rule", f"violations={risk_errors}")
    v.check(all(row["next_action"] for row in active if row["risk_status"] in ("Red", "Amber")),
            "Every at-risk account has a next action")
    mapping_by_account = defaultdict(list)
    uat_by_account = defaultdict(list)
    runs_by_account = defaultdict(list)
    usage_by_account = defaultdict(list)
    milestones_by_account = defaultdict(list)
    for row in mappings:
        mapping_by_account[row["account_id"]].append(row)
    for row in uat_results:
        uat_by_account[row["account_id"]].append(row)
    for row in runs:
        runs_by_account[row["account_id"]].append(row)
    for row in usage:
        usage_by_account[row["account_id"]].append(row)
    for row in milestones:
        milestones_by_account[row["account_id"]].append(row)
    derivative_errors = 0
    first_value_errors = 0
    milestone_first_value_errors = 0
    milestone_order_errors = 0
    for account in accounts:
        account_id = account["account_id"]
        account_mappings = mapping_by_account[account_id]
        mapping_rate = sum(
            row["mapping_status"] == "Mapped" for row in account_mappings
        ) / len(account_mappings)
        account_uat = uat_by_account[account_id]
        uat_rate = sum(row["status"] == "Passed" for row in account_uat) / len(account_uat)
        recent_runs = [
            row for row in runs_by_account[account_id]
            if row["run_date"] >= "2026-06-24"
        ]
        recent_success = (
            sum(row["status"] == "SUCCESS" for row in recent_runs) / len(recent_runs)
            if recent_runs else 1.0
        )
        readiness = 0.4 * mapping_rate + 0.3 * uat_rate + 0.3 * recent_success
        if (
            not close(account["mapping_coverage"], mapping_rate)
            or not close(account["uat_pass_rate"], uat_rate)
            or not close(account["recent_integration_success_rate"], recent_success)
            or not close(account["readiness_rate"], readiness)
        ):
            derivative_errors += 1
        eligible_usage_dates = [
            row["usage_date"] for row in usage_by_account[account_id]
            if int(row["active_users"]) >= 3
            and int(row["successful_syncs"]) >= 1
            and float(row["data_acceptance_rate"]) >= 0.95
            and int(row["key_workflows_completed"]) >= 1
        ]
        first_value = min(eligible_usage_dates) if eligible_usage_dates else ""
        expected_ttfv = (
            (dt.date.fromisoformat(first_value) - dt.date.fromisoformat(account["kickoff_date"])).days
            if first_value else ""
        )
        if (
            account["first_value_date"] != first_value
            or str(account["time_to_first_value_days"]) != str(expected_ttfv)
        ):
            first_value_errors += 1
        first_value_milestone = next(
            row for row in milestones_by_account[account_id]
            if row["milestone"] == "First value"
        )
        if first_value_milestone["actual_date"] != first_value:
            milestone_first_value_errors += 1
        actual_dates = [
            row["actual_date"]
            for row in sorted(
                milestones_by_account[account_id],
                key=lambda row: int(row["stage_order"]),
            )
            if row["actual_date"]
        ]
        if actual_dates != sorted(actual_dates):
            milestone_order_errors += 1
    v.check(
        derivative_errors == 0,
        "Every readiness component recomputes from mapping, UAT and recent runs",
        f"violations={derivative_errors}",
    )
    v.check(
        first_value_errors == 0,
        "Every first-value date and TTFV recomputes from usage acceptance conditions",
        f"violations={first_value_errors}",
    )
    v.check(
        milestone_first_value_errors == 0,
        "Account and lifecycle milestone use one canonical first-value date",
        f"violations={milestone_first_value_errors}",
    )
    v.check(
        milestone_order_errors == 0,
        "Completed lifecycle milestones are chronological",
        f"violations={milestone_order_errors}",
    )
    blocker_accounts = {row["account_id"] for row in blockers if row["status"] == "Open"}
    v.check(
        all(row["account_id"] in blocker_accounts for row in active if row["risk_status"] in ("Red", "Amber")),
        "Every at-risk active account has an open intervention record",
    )
    risk_chart = next(
        chart for chart in artifact["manifest"]["charts"]
        if chart["id"] == "risk_matrix"
    )
    v.check(
        risk_chart["type"] == "horizontalBar"
        and risk_chart["encodings"]["x"].get("field") == "account_risk_label"
        and risk_chart["encodings"]["y"].get("field") == "readiness_rate"
        and risk_chart["encodings"].get("color", {}).get("field") == "risk_status"
        and "size" not in risk_chart["encodings"],
        "Risk/readiness view directly labels accounts and visibly encodes readiness and risk",
    )
    risk_rows = artifact["snapshot"]["datasets"]["risk_queue"]
    expected_order = sorted(
        risk_rows,
        key=lambda row: (
            {"Red": 1, "Amber": 2, "Green": 3}[row["risk_status"]],
            int(row["days_to_committed_go_live"]),
            row["account_id"],
        ),
    )
    v.check(
        risk_rows == expected_order
        and all(
            row["account_id"] in row["account_risk_label"]
            and row["risk_status"].upper() in row["account_risk_label"]
            and f"{int(row['days_to_committed_go_live']):+d} days" in row["account_risk_label"]
            for row in risk_rows
        ),
        "Risk/readiness rows are critical-first and labels carry account, risk and days-to-committed",
    )
    for relative in ("docs/openapi.yaml", "docs/postman_collection.json", "docs/source-to-target-mapping.csv", "docs/uat-plan.md", "docs/go-live-runbook.md", "docs/raci.md"):
        v.check((project / relative).is_file(), f"Implementation evidence exists: {relative}")
    v.check("example.invalid" in (project / "docs/postman_collection.json").read_text(encoding="utf-8"),
            "API example uses a reserved non-production domain")
    scenario = read_json(project / "data/scenario-manifest.json")
    scenario_accounts = {
        account_id
        for item in scenario.get("injected_scenarios", [])
        for account_id in item.get("accounts", [])
    }
    v.check(
        scenario_accounts == {row["account_id"] for row in active if row["risk_status"] in ("Red", "Amber")},
        "Scenario manifest discloses every active intervention account",
    )
    return v.close()


VALIDATORS = {
    "commercial": validate_commercial,
    "reliability": validate_reliability,
    "integration": validate_integration,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", choices=["all", *PROJECTS], default="all")
    args = parser.parse_args()
    selected = PROJECTS.items() if args.project == "all" else [(args.project, PROJECTS[args.project])]
    reports = [VALIDATORS[name](path) for name, path in selected]
    result = {
        "status": "PASS" if all(report["status"] == "PASS" for report in reports) else "FAIL",
        "projects": reports,
        "totals": {
            "checks": sum(report["check_count"] for report in reports),
            "failures": sum(report["failure_count"] for report in reports),
        },
    }
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
