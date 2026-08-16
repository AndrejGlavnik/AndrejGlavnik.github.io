
# Methodology and limitations

The generator combines fixed product economics, channel and market factors, weekday and seasonal effects, a bounded deterministic actual-demand noise term and explicit promotion/supply scenarios. Promotion uplift combines category price elasticity with a disclosed mechanic-specific execution lift (Feature 25%, Display 35%, Bundle 22%, Price cut 8%); a saturation factor is applied at 30% discount. Every discount band spans all four mechanics. The locked forecast is generated independently from ex-ante calendar and planning inputs before each month, so realized daily noise cannot leak into forecast accuracy. The exact magnitudes are calculated after generation; no headline KPI is manually typed into the dashboard.

Promotion ROI compares actual scenario contribution with a modeled, model-derived no-promotion baseline. The response and execution assumptions are fictional scenario inputs, not fitted estimates; the result is useful for demonstrating analytical method, not for making causal claims about a real promotion.
