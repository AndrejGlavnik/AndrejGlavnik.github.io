
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
