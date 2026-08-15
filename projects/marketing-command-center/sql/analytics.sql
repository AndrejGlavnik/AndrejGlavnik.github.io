

-- DASHBOARD: executive summary
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

-- DASHBOARD: monthly trend
SELECT s.month,
       ROUND(SUM(s.net_revenue_eur), 2) AS actual_revenue,
       ROUND(MAX(b.budget_revenue), 2) AS budget_revenue,
       ROUND(SUM(s.gross_profit_eur), 2) AS gross_profit
FROM fact_sales s
JOIN (SELECT month, SUM(budget_revenue_eur) AS budget_revenue
      FROM fact_budget_forecast GROUP BY month) b ON b.month = s.month
GROUP BY s.month ORDER BY s.month;

-- DASHBOARD: market performance
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

-- DASHBOARD: promotion effectiveness
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

-- DASHBOARD: product detail
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

-- DASHBOARD: executed quality checks
SELECT "check" AS "check", status, result FROM quality_checks ORDER BY "check";
