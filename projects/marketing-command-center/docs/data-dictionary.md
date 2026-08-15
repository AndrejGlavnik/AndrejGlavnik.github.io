
# Data dictionary

## fact_sales

One row per date × SKU × market × channel. Revenue is expressed in EUR. `baseline_units` is a model-generated no-promotion planning baseline.

## fact_budget_forecast

One row per month × SKU × market × channel containing budget, ex-ante forecast basis, lock date and locked unit/revenue forecast. Forecast inputs exclude realized daily demand noise.

## fact_promotion

One row per promotion with date window, discount, execution mechanic, disclosed mechanic-specific lift assumption, activation cost, modeled uplift and derived scenario ROI. Each discount band spans all four mechanics so discount depth is not a proxy for one execution type.
