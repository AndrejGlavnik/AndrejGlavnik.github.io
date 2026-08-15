
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
