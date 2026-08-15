
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
