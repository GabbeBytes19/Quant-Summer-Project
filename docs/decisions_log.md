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

### Decision: Add synthetic data fixtures for local development instead of hitting the real API every run
- **Alternatives considered:** just re-running against the live Open-Meteo API each time; mocking the HTTP layer with a library (e.g. `responses`/`requests-mock`)
- **Reason:** While iterating on `bayesian_model.py` in notebook 04, repeatedly re-running the notebook to catch syntax/logic errors kept hitting Open-Meteo's minutely rate limit (`fetch_data` and `fetch_previous_forecast_data` both failing with "Minutely API request limit exceeded"), which blocked fast iteration. Added `tests/fixtures/synthetic_data.py` with `synthetic_actual_df()` and `synthetic_previous_df()` — fake dataframes matching the exact schema/column names of the real API responses (10 synthetic days, hourly resolution for the forecast side, with a small fixed warm bias baked into the forecast data so it isn't suspiciously perfect). These can be swapped in for the real fetch functions during development (by reassigning `fetcher.fetch_data`/`fetcher.fetch_previous_forecast_data`) so the whole pipeline runs on fake data with zero API calls until the code is confirmed working, then swapped back to the real API.
- **Date:** 2026-07-19

## Models

### Decision: Use Open-Meteo's Historical Forecast API (historical-forecast-api.open-meteo.com) for σ_forecast estimation
- **Alternatives considered:** the standard live Forecast API's rolling past_days/forecast_days window (only ~90 days, mistakenly hit first); a placeholder/assumed forecast-uncertainty value instead of real data; a different third-party weather API (e.g. Meteostat, Visual Crossing)
- **Reason:** The Bayesian model's likelihood needs σ_forecast (how far off forecasts typically are), estimated by pairing historical forecast values against actual outcomes for the same dates. Initially hit what looked like a ~90-day data constraint, but that came from calling the wrong Open-Meteo product (the live forecast endpoint's short rolling window). The correct dedicated endpoint for this, `historical-forecast-api.open-meteo.com/v1/forecast`, allows dates from 2016-01-01 to the present (~10 years) — far more than needed for a solid estimate. Usable *paired* data (forecast + known actual) only runs through the current date, not the endpoint's future-facing forecast days. No other API needed.
- **Date:** 2026-07-13

### Decision: Superseded above — use Open-Meteo's Previous Runs API (hourly, lead-time-specific) instead of Historical Forecast API for σ_forecast
- **Alternatives considered:** continuing with the Historical Forecast API's `daily=temperature_2m_max` endpoint (see decision above); falling back to an assumed/placeholder σ_forecast value instead of real data; a different third-party weather API
- **Reason:** After pairing `predicted_temp` against `actual_temp` for ~9 years of data, every single day came back with *exactly* zero error — not close, identical. Root cause: the Historical Forecast API's plain daily endpoint stitches together the first hours of each successive model run into a continuous timeseries that closely tracks actual conditions — it's effectively a near-real-time reconstruction, not a genuine N-days-ahead forecast, which is why it matched the archive/actuals almost exactly. The Previous Runs API instead gives genuine lead-time-specific forecasts via hourly parameters with a suffix (e.g. `temperature_2m_previous_day1` = value predicted 24h before valid time, up to `_previous_day7`). This requires aggregating 24 hourly values per day into a daily max, and accepting a much shorter available history (~2021 for GFS, ~2024 for other models, vs. the ~2016+ depth the Historical Forecast API appeared to offer). Chose to build this properly with real hourly data rather than fall back to a placeholder value, since a genuinely data-driven estimate was worth the added complexity and reduced sample size.
- **Date:** 2026-07-13

### Decision: Correct for forecast bias by baking it into the likelihood mean, not by adjusting raw forecasts everywhere
- **Alternatives considered:** ignore the bias and use the raw forecast value as-is; manually subtract the bias at every call site that uses a forecast value
- **Reason:** Pairing `day1_max` (previous-runs, 1-day-ahead forecast) against `actual_temp` across 1,860 days gave a mean error of **+0.38°C** (expected ~0 for an unbiased forecast) and a spread of **σ_forecast = 1.18°C**. The +0.38°C indicates a systematic warm bias — forecasts run slightly hotter than what actually happens, on average — separate from σ_forecast, which measures typical day-to-day error size regardless of direction. Since 0.38°C is a non-trivial fraction (~1/3) of σ_forecast, it's worth correcting rather than ignoring. Rather than subtracting the bias manually wherever a forecast value is used, the correction is applied once, inside the likelihood-mean computation for the Bayesian posterior update — so any caller gets an already-debiased estimate.
- **Date:** 2026-07-19

---

## Evaluation

### Decision: Multi-category (per-day) Brier score, not flat per-(day,bucket) averaging
- **Alternatives considered:** flattening every `(day, bucket)` pair into one independent sample and computing a plain binary-style Brier score over all of them (dividing by `T·B`)
- **Reason:** Each day's bucket probabilities aren't independent draws — they're one probability distribution over mutually exclusive outcomes (they sum to ~1, and exactly one bucket is correct per day). Treating `(day, bucket)` pairs as flat independent samples would ignore that structure. Instead: sum squared error across all buckets *within* a day first, then average across days. This is Brier's original 1950 multi-category formulation, built for exactly this case (multi-category weather forecasts). Consequence: the score's range becomes [0, 2] instead of [0, 1] — worth remembering so a computed value >1 isn't mistaken for a bug.
- **Log loss follows the same per-day convention** — since the outcome vector is one-hot, it collapses to `-log(f_{t,b*})` (the probability the model put on the bucket that actually happened), averaged over days.
- **ECE is the one exception** — it deliberately uses flat `(day, bucket)` pairs as its unit of analysis (`N = T·B`), since calibration binning is about individual predicted-probability values, not per-day distributions. Not an inconsistency, just a different question being asked.
- See `math_reference.md` → Evaluation for the full formulas.
- **Date:** 2026-07-20

---

## Phase 1 Summary

**Status: Phase 1 (probabilistic models + calibration, no Polymarket integration) is complete as of 2026-07-24.**

- Three models built and evaluated end-to-end: Gaussian baseline (climatology only), KDE (climatology only), and a Bayesian model (Gaussian climatological prior + forecast-conditioned likelihood via Normal-Normal conjugate update, debiased for the +0.38°C systematic warm bias in the 1-day-ahead forecast).
- IS/OOS split: climatological prior built from 2000-01-01–2015-01-01 (no forecast pairing needed); scored out-of-sample on 2017-01-01–2026-06-28, yielding 1,135 days with real paired forecast/actual data (Open-Meteo Previous Runs API coverage starts ~2021-05-01; earlier OOS dates are safely dropped by the join since they have no real forecast to pair).
- Evaluation uses 11 buckets of 1°C each (25–36°C), matching Polymarket Hong Kong's actual market structure, scored via the multi-category (per-day) Brier score and log loss.
- **Results (Brier / log loss, lower is better):** Gaussian 0.902 / 2.444, KDE 0.903 / 2.384, Bayesian 0.765 / 1.598.
- **Skill scores vs. Gaussian baseline:** Bayesian beats Gaussian by ~15.2% (Brier) and ~34.6% (log loss). KDE vs. Gaussian is statistically a wash (~0% Brier skill) once the earlier IS/OOS look-ahead leak was fixed — KDE's initial apparent edge over Gaussian was an artifact of the leak, not a real advantage.
- **Calibration:** no model ever assigns more than ~40-49% confidence to any single 1°C bucket in this dataset — real forecast uncertainty (σ_forecast ≈ 1.18°C) still spreads probability across 2-3 adjacent buckets even after forecast-conditioning. Gaussian/KDE show inconsistent-direction miscalibration (underconfident at low predicted probabilities, overconfident in the mid-range). Bayesian is comparably or better calibrated across all its bins, with only mild overconfidence at its two highest-confidence bins.
- **Bottom line:** Bayesian's lower error is not just a confidence artifact — it is also reasonably well-calibrated relative to the climatology-only models. Conditioning on the forecast earns its added complexity.
- **Reproducibility:** `python run_experiment.py` from the repo root runs the full pipeline (fetch → clean → build prior → build OOS pairs → score all 3 models → print scores, skill scores, and calibration bins) end-to-end from `config/settings.py`, with no notebook required.
- **Date:** 2026-07-24

---

## Risk

*(Fill in as you make risk management decisions)*
