# Decisions Log

A running record of key decisions and the reasoning behind them.
Update this whenever you make a non-obvious choice. Invaluable for interviews.

Format per entry:
- **Decision:** what was chosen
- **Alternatives considered:** what else was on the table
- **Reason:** why this choice was made
- **Date:** when it was decided

---

## Project Setup

### Decision: Use weather data as the primary domain
- **Alternatives considered:** sports outcomes, election markets, crypto volatility
- **Reason:** Weather has clean historical data (Open-Meteo), free API, objectively measurable outcomes, and direct Polymarket markets. Removes ambiguity about ground truth.
- **Date:** 2026-06-28

### Decision: Phased build — model first, Polymarket second
- **Alternatives considered:** integrating Polymarket from day 1
- **Reason:** Integrating the market too early risks building API code instead of understanding probability. The model must be validated before comparing it to anything. Interviewers care about calibration, not API connectivity.
- **Date:** 2026-06-28

### Decision: Bucket probability formulation (P(a < T ≤ b))
- **Alternatives considered:** binary threshold (P(T > threshold)), regression (predict exact temperature)
- **Reason:** Polymarket Hong Kong temperature markets resolve to 1°C buckets (e.g. "32°C" means the high fell in [31.5, 32.5)). Matching the market structure exactly allows direct comparison of model probabilities to market-implied probabilities. Each bucket is still a binary YES/NO contract — proper scoring rules (Brier, log loss) and Kelly criterion still apply.
- **Date:** 2026-07-08

### Decision: City changed to Hong Kong, threshold 30°C
- **Alternatives considered:** Linköping (25°C threshold), Seoul
- **Reason:** Hong Kong has active Polymarket daily temperature markets. Linköping does not. 30°C is a natural midpoint in the Hong Kong market's bucket range (25°C–35°C+) and aligns with the subtropical summer climate. Hong Kong summer temperatures also fit a Gaussian well, making the baseline model more meaningful.
- **Date:** 2026-07-08

### Decision: Strict Jupyter/module separation
- **Alternatives considered:** all logic in notebooks, all logic in .py files
- **Reason:** Notebooks for research thinking, .py modules for production logic. This is how real quant teams work. Mixing them makes the repo look like a student project.
- **Date:** 2026-06-28

### Decision: Use polar insead of pandas
- ** Polar should be used for dataset
- ** Reason: ** Polar are much faster, slepless integration without copying. 
- **Date:** 2026-06-29
## Models

### Decision: Use Open-Meteo's Historical Forecast API (historical-forecast-api.open-meteo.com) for σ_forecast estimation
- **Alternatives considered:** the standard live Forecast API's rolling past_days/forecast_days window (only ~90 days, mistakenly hit first); a placeholder/assumed forecast-uncertainty value instead of real data; a different third-party weather API (e.g. Meteostat, Visual Crossing)
- **Reason:** The Bayesian model's likelihood needs σ_forecast (how far off forecasts typically are), estimated by pairing historical forecast values against actual outcomes for the same dates. Initially hit what looked like a ~90-day data constraint, but that came from calling the wrong Open-Meteo product (the live forecast endpoint's short rolling window). The correct dedicated endpoint for this, `historical-forecast-api.open-meteo.com/v1/forecast`, allows dates from 2016-01-01 to the present (~10 years) — far more than needed for a solid estimate. Usable *paired* data (forecast + known actual) only runs through the current date, not the endpoint's future-facing forecast days. No other API needed.
- **Date:** 2026-07-13

### Decision: Superseded above — use Open-Meteo's Previous Runs API (hourly, lead-time-specific) instead of Historical Forecast API for σ_forecast
- **Alternatives considered:** continuing with the Historical Forecast API's `daily=temperature_2m_max` endpoint (see decision above); falling back to an assumed/placeholder σ_forecast value instead of real data; a different third-party weather API
- **Reason:** After pairing `predicted_temp` against `actual_temp` for ~9 years of data, every single day came back with *exactly* zero error — not close, identical. Root cause: the Historical Forecast API's plain daily endpoint stitches together the first hours of each successive model run into a continuous timeseries that closely tracks actual conditions — it's effectively a near-real-time reconstruction, not a genuine N-days-ahead forecast, which is why it matched the archive/actuals almost exactly. The Previous Runs API instead gives genuine lead-time-specific forecasts via hourly parameters with a suffix (e.g. `temperature_2m_previous_day1` = value predicted 24h before valid time, up to `_previous_day7`). This requires aggregating 24 hourly values per day into a daily max, and accepting a much shorter available history (~2021 for GFS, ~2024 for other models, vs. the ~2016+ depth the Historical Forecast API appeared to offer). Chose to build this properly with real hourly data rather than fall back to a placeholder value, since a genuinely data-driven estimate was worth the added complexity and reduced sample size.
- **Date:** 2026-07-13

---

## Evaluation

*(Fill in as you make evaluation decisions)*

---

## Risk

*(Fill in as you make risk management decisions)*
