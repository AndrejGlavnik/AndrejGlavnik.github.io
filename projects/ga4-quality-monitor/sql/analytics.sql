-- Executive release decision
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

-- Weekly quality trend
SELECT strftime('%Y-W%W', run_date) AS week,
       ROUND(SUM(CASE WHEN status = 'PASS' THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 6) AS pass_rate,
       SUM(CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END) AS failures,
       SUM(CASE WHEN status = 'WARN' THEN 1 ELSE 0 END) AS warnings
FROM fact_quality_result GROUP BY week ORDER BY week;

-- Asset quality
SELECT asset_id,
       ROUND(SUM(CASE WHEN status = 'PASS' THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 6) AS pass_rate,
       SUM(CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END) AS failures,
       SUM(CASE WHEN status = 'WARN' THEN 1 ELSE 0 END) AS warnings
FROM fact_quality_result GROUP BY asset_id ORDER BY pass_rate ASC;

-- Latest reconciliation
SELECT asset_id,
       ROUND(ABS(dashboard_value - governed_value) / ABS(governed_value), 6)
       AS reconciliation_variance,
       ROUND(ABS(dashboard_value - governed_value) / ABS(governed_value) * 10000, 2)
       AS reconciliation_variance_bps
FROM fact_pipeline_run WHERE run_date = '2026-06-30'
ORDER BY reconciliation_variance DESC;

-- Failure evidence
SELECT run_date, asset_id, rule_name, severity, status, observed_value, threshold, affected_rows, owner
FROM fact_quality_result WHERE status <> 'PASS'
ORDER BY run_date DESC, CASE severity WHEN 'Critical' THEN 1 ELSE 2 END LIMIT 30;

-- Release gates
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

-- Incident root causes
SELECT root_cause, COUNT(*) AS incidents,
       SUM(CASE WHEN severity = 'Critical' THEN 1 ELSE 0 END) AS critical_incidents
FROM fact_incident GROUP BY root_cause ORDER BY incidents DESC, root_cause;
