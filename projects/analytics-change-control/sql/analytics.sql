-- Portfolio KPIs
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

-- Implementation funnel
SELECT milestone, MIN(stage_order) AS stage_order,
       SUM(CASE WHEN actual_date <> '' THEN 1 ELSE 0 END) AS completed_accounts
FROM fact_milestone GROUP BY milestone ORDER BY stage_order;

-- Connector reliability
SELECT connector_id,
       ROUND(SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 6) AS success_rate,
       ROUND(SUM(records_accepted) * 1.0 / SUM(records_received), 6) AS data_acceptance_rate,
       ROUND(AVG(latency_ms), 0) AS average_latency_ms,
       SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) AS failed_runs
FROM fact_integration_run GROUP BY connector_id ORDER BY success_rate ASC;

-- Cohort lead time
SELECT substr(kickoff_date, 1, 7) AS kickoff_month,
       ROUND(AVG(julianday(actual_go_live_date) - julianday(kickoff_date)), 2) AS average_lead_days,
       COUNT(*) AS completed_accounts
FROM dim_account WHERE project_status = 'Completed'
GROUP BY kickoff_month ORDER BY kickoff_month;

-- Intervention queue
SELECT account_id,
       account_id || ' | ' || UPPER(risk_status) || ' | '
         || printf('%+d days', days_to_committed_go_live) AS account_risk_label,
       CASE risk_status WHEN 'Red' THEN 1 WHEN 'Amber' THEN 2 ELSE 3 END AS risk_order,
       fictional_account_name, segment, days_to_committed_go_live,
       readiness_rate, mapping_coverage, uat_pass_rate,
       recent_integration_success_rate, risk_status, risk_reason, next_action
FROM dim_account WHERE project_status = 'Active'
ORDER BY risk_order, days_to_committed_go_live ASC, account_id ASC;

-- Error Pareto
SELECT CASE WHEN error_code = '' THEN 'NONE' ELSE error_code END AS error_code,
       COUNT(*) AS runs,
       SUM(records_rejected) AS rejected_records
FROM fact_integration_run WHERE status = 'FAILED'
GROUP BY error_code ORDER BY runs DESC;
