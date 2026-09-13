# Decisions Log

A running record of key decisions and the reasoning behind them.
Update this whenever you make a choice that isn't obvious. Invaluable for interviews.

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

### Decision: Phased build, model first, Polymarket second
- **Alternatives considered:** integrating Polymarket from day 1
- **Reason:** Integrating the market too early risks building API code instead of understanding probability. The model must be validated before comparing it to anything. Interviewers care about calibration, not API connectivity.
- **Date:** 2026-06-28

### Decision: Bucket probability formulation (P(a < T ≤ b))
- **Alternatives considered:** binary threshold (P(T > threshold)), regression (predict exact temperature)
- **Reason:** Polymarket Hong Kong temperature markets resolve to 1°C buckets (e.g. "32°C" means the high fell in [32, 33)). Matching the market structure exactly allows direct comparison of model probabilities to market implied probabilities. Each bucket is still a binary YES/NO contract, so proper scoring rules (Brier, log loss) and Kelly criterion still apply.
- **Date:** 2026-07-08

### Decision: City changed to Hong Kong, threshold 30°C
- **Alternatives considered:** Linköping (25°C threshold), Seoul
- **Reason:** Hong Kong has active Polymarket daily temperature markets. Linköping does not. 30°C is a natural midpoint in the Hong Kong market's bucket range (25°C–35°C+) and aligns with the subtropical summer climate. Hong Kong summer temperatures also fit a Gaussian well, making the baseline model more meaningful.
- **Date:** 2026-07-08

### Decision: Strict Jupyter/module separation
- **Alternatives considered:** all logic in notebooks, all logic in .py files
- **Reason:** Notebooks for research thinking, .py modules for production logic. This is how real quant teams work. Mixing them makes the repo look like a student project.
- **Date:** 2026-06-28

### Decision: Use Polars instead of pandas
- **Decision:** Polars should be used for the dataset.
- **Reason:** Polars is much faster, with seamless integration and no unnecessary copying.
- **Date:** 2026-06-29

### Decision: Add synthetic data fixtures for local development instead of hitting the real API every run
- **Alternatives considered:** just rerunning against the live Open-Meteo API each time, or mocking the HTTP layer with a library (e.g. `responses`/`requests-mock`)
- **Reason:** While iterating on `bayesian_model.py` in notebook 04, repeatedly rerunning the notebook to catch syntax/logic errors kept hitting Open-Meteo's minutely rate limit (`fetch_data` and `fetch_previous_forecast_data` both failing with "Minutely API request limit exceeded"), which blocked fast iteration. Added `tests/fixtures/synthetic_data.py` with `synthetic_actual_df()` and `synthetic_previous_df()`, fake dataframes matching the exact schema/column names of the real API responses (10 synthetic days, hourly resolution for the forecast side, with a small fixed warm bias baked into the forecast data so it isn't suspiciously perfect). These can be swapped in for the real fetch functions during development (by reassigning `fetcher.fetch_data`/`fetcher.fetch_previous_forecast_data`) so the whole pipeline runs on fake data with zero API calls until the code is confirmed working, then swapped back to the real API.
- **Date:** 2026-07-19

## Models

### Decision: Use Open-Meteo's Historical Forecast API (historical-forecast-api.open-meteo.com) for σ_forecast estimation
- **Alternatives considered:** the standard live Forecast API's rolling past_days/forecast_days window (only ~90 days, mistakenly hit first), a placeholder/assumed forecast uncertainty value instead of real data, or a different third party weather API (e.g. Meteostat, Visual Crossing)
- **Reason:** The Bayesian model's likelihood needs σ_forecast (how far off forecasts typically are), estimated by pairing historical forecast values against actual outcomes for the same dates. Initially hit what looked like a ~90 day data constraint, but that came from calling the wrong Open-Meteo product (the live forecast endpoint's short rolling window). The correct dedicated endpoint for this, `historical-forecast-api.open-meteo.com/v1/forecast`, allows dates from 2016-01-01 to the present (~10 years), far more than needed for a solid estimate. Usable *paired* data (forecast + known actual) only runs through the current date, not the endpoint's future facing forecast days. No other API needed.
- **Date:** 2026-07-13

### Decision: Superseded above, use Open-Meteo's Previous Runs API (hourly, lead time specific) instead of Historical Forecast API for σ_forecast
- **Alternatives considered:** continuing with the Historical Forecast API's `daily=temperature_2m_max` endpoint (see decision above), falling back to an assumed/placeholder σ_forecast value instead of real data, or a different third party weather API
- **Reason:** After pairing `predicted_temp` against `actual_temp` for ~9 years of data, every single day came back with *exactly* zero error, not close, identical. The root cause was that the Historical Forecast API's plain daily endpoint stitches together the first hours of each successive model run into a continuous timeseries that closely tracks actual conditions. It's effectively a near real time reconstruction, not a genuine N day ahead forecast, which is why it matched the archive/actuals almost exactly. The Previous Runs API instead gives genuine lead time specific forecasts via hourly parameters with a suffix (e.g. `temperature_2m_previous_day1` = value predicted 24h before valid time, up to `_previous_day7`). This requires aggregating 24 hourly values per day into a daily max, and accepting a much shorter available history (~2021 for GFS, ~2024 for other models, vs. the ~2016+ depth the Historical Forecast API appeared to offer). Chose to build this properly with real hourly data rather than fall back to a placeholder value, since a genuinely data driven estimate was worth the added complexity and reduced sample size.
- **Date:** 2026-07-13

### Decision: Correct for forecast bias by baking it into the likelihood mean, not by adjusting raw forecasts everywhere
- **Alternatives considered:** ignore the bias and use the raw forecast value as is, or manually subtract the bias at every call site that uses a forecast value
- **Reason:** Pairing `day1_max` (previous runs, 1 day ahead forecast) against `actual_temp` across 1,860 days gave a mean error of **+0.38°C** (expected ~0 for an unbiased forecast) and a spread of **σ_forecast = 1.18°C**. The +0.38°C indicates a systematic warm bias, forecasts run slightly hotter than what actually happens on average, separate from σ_forecast, which measures typical day to day error size regardless of direction. Since 0.38°C is a meaningful fraction (~1/3) of σ_forecast, it's worth correcting rather than ignoring. Rather than subtracting the bias manually wherever a forecast value is used, the correction is applied once, inside the likelihood mean computation for the Bayesian posterior update, so any caller gets an already debiased estimate.
- **Date:** 2026-07-19

---

## Evaluation

### Decision: Multi category (per day) Brier score, not flat per (day, bucket) averaging
- **Alternatives considered:** flattening every `(day, bucket)` pair into one independent sample and computing a plain binary style Brier score over all of them (dividing by `T·B`)
- **Reason:** Each day's bucket probabilities aren't independent draws, they're one probability distribution over mutually exclusive outcomes (they sum to ~1, and exactly one bucket is correct per day). Treating `(day, bucket)` pairs as flat independent samples would ignore that structure. Instead, the squared error is summed across all buckets *within* a day first, then averaged across days. This is Brier's original 1950 multi category formulation, built for exactly this case (multi category weather forecasts). As a result, the score's range becomes [0, 2] instead of [0, 1], which is worth remembering so a computed value >1 isn't mistaken for a bug.
- **Log loss follows the same per day convention.** Since the outcome vector is one hot, it collapses to `-log(f_{t,b*})` (the probability the model put on the bucket that actually happened), averaged over days.
- **ECE is the one exception.** It deliberately uses flat `(day, bucket)` pairs as its unit of analysis (`N = T·B`), since calibration binning is about individual predicted probability values, not per day distributions. Not an inconsistency, just a different question being asked.
- See `math_reference.md` → Evaluation for the full formulas.
- **Date:** 2026-07-20

---

## Phase 1 Summary

**Status.** Phase 1 (probabilistic models + calibration, no Polymarket integration) is complete as of 2026-07-24.

- Three models built and evaluated end to end. Gaussian baseline (climatology only), KDE (climatology only), and a Bayesian model (Gaussian climatological prior updated via a conjugate update between two normal distributions, debiased for the +0.38°C systematic warm bias in the 1 day ahead forecast).
- IS/OOS split. Climatological prior built from 2000-01-01 to 2016-12-31 (no forecast pairing needed), scored out of sample on 2017-01-01 to 2026-06-28, yielding 1,135 days with real paired forecast/actual data (Open-Meteo Previous Runs API coverage starts ~2021-05-01, earlier OOS dates are safely dropped by the join since they have no real forecast to pair).
- Evaluation uses 11 buckets of 1°C each (25–36°C), matching Polymarket Hong Kong's actual market structure, scored via the multi category (per day) Brier score and log loss.
- **Results (Brier / log loss, lower is better).** Gaussian 0.902 / 2.444, KDE 0.903 / 2.384, Bayesian 0.765 / 1.598.
- **Skill scores vs. Gaussian baseline.** Bayesian beats Gaussian by ~15.2% (Brier) and ~34.6% (log loss). KDE vs. Gaussian is statistically a wash (~0% Brier skill) once the earlier IS/OOS look ahead leak was fixed, KDE's initial apparent edge over Gaussian was an artifact of the leak, not a real advantage.
- **Calibration.** No model ever assigns more than ~40-49% confidence to any single 1°C bucket in this dataset. Real forecast uncertainty (σ_forecast ≈ 1.18°C) still spreads probability across 2-3 adjacent buckets even after forecast conditioning. Gaussian/KDE show inconsistent direction miscalibration (underconfident at low predicted probabilities, overconfident in the mid range). Bayesian is comparably or better calibrated across all its bins, with only mild overconfidence at its two highest confidence bins.
- **Bottom line.** Bayesian's lower error is not just a confidence artifact. It is also reasonably well calibrated relative to the climatology only models. Conditioning on the forecast earns its added complexity.
- **Reproducibility.** `python run_experiment.py` from the repo root runs the full pipeline (fetch → clean → build prior → build OOS pairs → score all 3 models → print scores, skill scores, and calibration bins) end to end from `config/settings.py`, with no notebook required.
- **Date:** 2026-07-24

---

## Pricing & Edge

### Decision: `price_paid`/edge use the price history column `p`, not the settlement snapshot `market_prob`
- **Alternatives considered:** using `market_prob` (from `outcomePrices.list.first()`, set in `add_market_prob_column`)
- **Reason:** every row in `df_result` has already passed `filter_resolved`, so every market is closed. `outcomePrices` on a fully resolved binary market is the *final payout*, exactly `1` for the winning side, `0` for the losing side, always, not a snapshot of what anyone actually traded at. `p` (joined via `join_asof` against real price history, at `target = endDate - 1 day`, specifically chosen to land *before* resolution) holds genuine intermediate trading prices instead. This was confirmed empirically. Filtering `price_paid != 0 and != 1` initially returned **zero rows** when built from `market_prob`, proof the column was always exactly 0 or 1, never anything else.
- **Date:** 2026-08-11

### Decision: `effective_edge_flag` requires *both* `abs(edge) >= MIN_EDGE` and `abs(effective_edge) >= MIN_EFFECTIVE_EDGE`, not either alone
- **Alternatives considered:** checking only the raw edge threshold, checking only the fee adjusted threshold, or treating the two as alternatives (OR) instead of both required (AND)
- **Reason:** the two thresholds answer different questions, "is the raw mispricing big enough to notice" vs. "is it still big enough once costs are subtracted." A row can clear one and fail the other (e.g. raw edge is large but shrinks below the effective bar once spread/fees are subtracted). Both need to hold for a trade to actually be worth taking.
- **Date:** 2026-08-11

### Decision: flat assumed spread of 0.05 (`settings.ASSUMED_SPREAD`, read by `effective_edge()`), not real per market historical spread
- **Alternatives considered:** Polymarket's own live `/spread`/`/book` CLOB endpoints (only cover currently open markets, every market here is closed, so these return "no orderbook exists" for all of them), **Dome API** (real, but Polymarket acquired Dome on 2026-02-19 and shut down all Dome APIs by 2026-04-28, confirmed dead, not just gated), **PolymarketData.co** (real, explicitly paid/tiered), **Bitquery** (provides trade data, not order book/bid ask data, wrong kind of data entirely, also $39+/month), and **pmxt** (real open source library, but its order book fetch appears live only with no historical/date parameter, plus its own API key + Node.js dependency)
- **Reason:** full L2 order book history is expensive to store, so every option either charges, expects self hosted chain indexing, or only kept trade prices (which can't reconstruct a spread, since a fill price isn't the same as the surrounding unfilled bid/ask). Four independent sources hit the same wall. `0.05` (half of Polymarket's own "$0.10 = unusually wide, stop showing midpoint" threshold) is a reasonable moderate illiquidity assumption, not a random guess. `spread` only affects the `effective_edge_flag` eligibility filter. It is *not* deducted from a trade's realized `profit` (only `FEE_RATE` is).
- **Date:** 2026-08-11 *(settled, not an open item to revisit without a genuinely new, verified free/simple source appearing)*

---

## Risk

### Decision: Kelly is two sided, negative `f*` means "bet the No side," not "don't bet"
- **Alternatives considered:** clamping `f*` to `[0, 1]` and never betting when the model disagrees with the market in the negative direction (the original `math_reference.md` plan)
- **Reason:** `edge = P_model - P_market` is two sided by construction, positive means the model thinks Yes is underpriced, negative means it thinks Yes is *overpriced* (i.e. No is underpriced). Clamping negative `f*` to 0 would silently discard exactly half of the tradeable signal. `side` is decided from the sign of `edge` in `backtest/engine.py`, and both the probability and the price fed into `kelly_criterion` are flipped to `1 - p_model`/`1 - price` for No side rows, so Kelly is evaluated against whichever side is actually being bet, not always the raw Yes framing.
- **Date:** 2026-08-11

### Decision: VaR / Expected Shortfall / max drawdown computed on realized backtest `profit`/`cumulative_profit`, not on raw market data
- **Alternatives considered:** (accidentally, mid session) computing these on `outcomePrices` or on `p` (the market price column)
- **Reason:** `risk/metrics.py` was originally pointed at the wrong columns. Market price data describes the *markets*, not the *strategy's* realized gains and losses. VaR/ES need the distribution of per trade `profit`, and max drawdown needs the running peak of `cumulative_profit`. `rolling_max_dd` also needed a genuine fix, not just a column swap. It originally only computed the running peak (`cum_max()`) and never took the final subtraction step to turn that into an actual drawdown value.
- **Date:** 2026-08-11

### Decision: `stake` computed per trade via `kelly_criterion`, not a flat constant
- **Alternatives considered:** a flat hardcoded stake (used as a temporary placeholder mid session, same reasoning as the spread placeholder)
- **Reason:** unlike spread, there's no external data problem here. `kelly_criterion` only needs `p_model` and `market_odds`, both of which already exist in the pipeline. A flat stake made every loss identical in size, which made VaR and Expected Shortfall trivially collapse to that one constant. That was informative, it meant the placeholder was working as expected, but it wasn't measuring anything real about the strategy's actual risk. Both the probability and the price side of the Kelly call are attached as dataframe columns early (in `prob_market_v_model`) specifically so they survive every downstream `.filter()` in `engine()` in alignment with everything else, rather than staying at their original, longer, pre filter length.
- **Date:** 2026-08-11

---

## Backtest

### Decision: ground truth (win/loss flag) computed once and shared across all models, not recomputed per model
- **Alternatives considered:** calling `run_eval_loop_polymarket` separately for each model (gauss/KDE/Bayesian), as an early draft did
- **Reason:** whether a bucket actually occurred is a fact about reality, independent of which model is being evaluated against it. Computing it three times repeats the same `df_pair` loop three times for identical output, which is wasteful, and it obscures which of the three (identical) results should actually feed into the backtest.
- **Date:** 2026-08-11

### Decision: day independent and day dependent probability functions get two separate factory patterns, not one generic mechanism
- **Alternatives considered:** a single factory shape for all three models
- **Reason:** `run_eval_loop_polymarket` needs a uniform `day → (low, high) → probability` interface, but Gaussian/KDE don't actually depend on which day it is (same historical distribution every time), while Bayesian's posterior genuinely depends on that day's specific forecast. `make_static_factory(prob_fn)` handles the day independent case generically (accepts a day, ignores it, always returns the same wrapped function), reused for both Gaussian and KDE instead of two near identical hand written functions. Bayesian needs its own dedicated three level closure that actually threads the day through to `posterior_probability(day, low, high)`.
- **Date:** 2026-08-11

### Decision: filter out rows where `price_paid == 0` or `== 1` before computing profit
- **Reason:** a price of exactly 0 or 1 produces a division by zero (infinite) payout in the Kelly/profit formula. These values show up because the price history join can land on a moment right at/after resolution rather than a genuine pre resolution trading price, not a real trading decision under uncertainty, so it's excluded rather than clipped to an arbitrary floor value.
- **Date:** 2026-08-11

### Decision: `cumsum()` must run *after* sorting by date, not before
- **Reason:** `cumulative_profit` is only meaningful as a chronological running total. Computing it before the final `.sort("date")` accumulates in whatever arbitrary row order the data happened to be in internally, then just relabels the (wrong) numbers with the correct dates afterward. This was caught by checking the arithmetic manually (`cumulative_profit[i] != cumulative_profit[i-1] + profit[i]` in date order) rather than assuming a clean run meant correct output.
- **Date:** 2026-08-11

---

## Phase 2/3 Summary

**Status.** The full edge → Kelly → backtest → risk pipeline is built and runs end to end via `python run_experiment.py`, alongside the original Phase 1 pipeline, as of 2026-08-11.

- Model comparison (Phase 1, reconfirmed). Bayesian beats Gaussian/KDE on both Brier score and log loss.
- Backtest results are directionally consistent with that finding, though the exact numbers vary run to run since Polymarket's dataset is live and constantly growing/updating (see "Known limitations" below). In one representative run, Bayesian ended with the highest cumulative profit and the *lowest* VaR, Expected Shortfall, and max drawdown of the three models, i.e. it won on every axis, not just accuracy.
- **Known limitations, tracked as open items (see `roadmap.md` Week 10).**
  - `stake` and `spread` were both temporary flat placeholders earlier in the session. `stake` is now real (per trade Kelly), and `spread` is a **permanent** documented assumption (see Pricing & Edge above), not a temporary one.
  - Backtest results are not perfectly reproducible run to run at even the same total row count, the underlying Polymarket dataset is live (unbounded, always current), `settings.OOS_END` is defined as "yesterday" (shifts daily), and individual markets can update between runs.
  - IS/OOS results are not currently reported *separately* in the backtest (one combined result per model).
  - No Sharpe ratio, and no dedicated Kelly sensitivity notebook (`08_Risk_Analysis_Kelly.ipynb` still empty).
- **Date:** 2026-08-11

### Correction (2026-09-11): Sharpe ratio, Kelly sensitivity, and the IS/OOS item above
- Sharpe ratio is now implemented (`risk/metrics.py:sharpe_ratio`, printed via `backtest/pnl.py:get_pnl()`), and `notebooks/08_Risk_Analysis_Kelly.ipynb` now covers the Kelly sensitivity analysis (f* vs. edge, f* vs. market odds, plus a combined heatmap). Both items above are closed.
- The "IS/OOS not reported separately in the backtest" item above pointed at something real, but not what the wording said. Every Polymarket market falls inside the OOS window, so there was never an in sample slice of trades to split out. What the item should have said is that the Bayesian likelihood was fit on all of `df_pair`, including the scored day and later days. See the 2026-09-13 entry below for the fix.

---

## Review fixes and rerun (2026-09-13)

A full code review on 2026-09-12 surfaced a set of bugs. All were reproduced with tests first (`tests/test_regressions.py`), then fixed.

- **Bayesian look ahead.** `bayesian_interference` called `compute_forecast_error(df_pair)` on the entire paired dataset for every day, so the forecast bias and sigma for day t included day t's own outcome and every later day. Fix in `models/bayesian_model.py`, the error statistics now come from `df_pair.filter(pl.col("date") < day)`, an expanding window of earlier days only. `config/settings.py:MIN_FORECAST_HISTORY = 30` sets the warmup, and both eval loops in `evaluation/eval_loop.py` skip the first 30 rows of `df_pair` for every model so Gaussian, KDE, and Bayesian are scored on identical days.
- **`effective_edge` sign asymmetry.** `pricing/edge.py` subtracted spread/2 and the fee from the signed edge and then took `abs()`, so a No side edge of -0.06 became -0.105 and passed while a Yes side edge of +0.06 became 0.015 and failed. Costs are now applied to `abs(edge)` with the sign restored. Trade counts across models moved to within four of each other after the fix (644 to 648).
- **Unknown outcomes booked as No wins.** In `run_eval_loop_polymarket` the win/loss flag was `otherwise(0)`, so an open ended market or a day without ground truth counted as a loss for Yes and a win for No. The flag is now null in those cases and `backtest/engine.py` drops null flag rows before sizing.
- **Forecast fetch ignored its arguments.** `fetch_previous_forecast_data` hardcoded `past_days=1900` and no timezone. It now sends `start_date`, `end_date`, and `timezone=settings.TIMEZONE`. Open-Meteo returns nulls for dates before its previous runs coverage (mid 2021), which `pair_dataframes` already drops, so the effective data range is unchanged but now follows `OOS_START` and aligns forecast days to Hong Kong local time like the actuals.
- **Null gap rule.** `clean_data` counted rows dropped after interpolation, which only ever counted leading or trailing nulls. It now rejects the dataset if the total null count exceeds `MAX_NULL_GAP` before interpolating.
- **Double fetch.** `run_experiment()` called `fetch_all_data()` and discarded the result before `run_system()` fetched again. Removed.

**Rerun results (2026-09-13, 1,976 resolved markets).**

| Model | Brier | Log loss | Profit | VaR | ES | Max DD | Sharpe (per trade) | Trades |
|---|---|---|---|---|---|---|---|---|
| Gaussian | 0.902 | 2.441 | 45.2 | 0.168 | 0.219 | 2.13 | 0.102 | 644 |
| KDE | 0.902 | 2.383 | 45.5 | 0.166 | 0.216 | 1.77 | 0.102 | 648 |
| Bayesian | 0.740 | 1.523 | 113.5 | 0.100 | 0.160 | 1.15 | 0.129 | 644 |

Skill scores over Gaussian, Bayesian 0.180 (Brier) and 0.376 (log loss). KDE vs. Gaussian 0.000 (Brier) and 0.024 (log loss).

- **Why Bayesian improved after removing the leak** (Brier 0.765 to 0.740, log loss 1.598 to 1.523, with Gaussian and KDE unchanged). The old code applied one bias averaged over 2021 to 2026 to every day. The forecast bias is not constant over that period, so early days were corrected with a number dominated by later years. The expanding window uses only what was known at the time and tracks the drift. Gaussian and KDE do not use the forecast, so they were unaffected by both the leak and the fix.
- **Calibration.** Bayesian predicted vs. observed by bucket, 0.011/0.018, 0.146/0.170, 0.249/0.246, 0.356/0.300, 0.418/0.399. Gaussian and KDE remain overconfident in their top bucket (0.242 predicted vs. 0.164 observed).
- **Date:** 2026-09-13
