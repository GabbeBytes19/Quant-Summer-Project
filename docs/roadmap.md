# Project Roadmap

Status as of 2026-09-13. Each week lists what was delivered, what "done" meant, and anything still open. Open items across the whole project are collected again under Week 10.

---

## Phase 1, Build the Brain (Weeks 1–5)
The goal is a working, calibrated probability model. No Polymarket yet.

---

### Week 1, Foundation

**Deliverables**
- All folders and files scaffolded.
- `config/settings.py` holds coordinates, date ranges, the event threshold, fee rate, edge thresholds, and the Kelly fraction. It is the only config file the code reads.
- `config/config.yaml` was scaffolded here but nothing reads it. Tracked for removal under Week 10.
- `.gitignore` covers `.env`, `__pycache__/`, `.ipynb_checkpoints/`, `.vscode/`, and `.DS_Store`. No API keys are needed anywhere in this project, Open-Meteo and Polymarket are both keyless, so the `.env` entry is defensive.
- `requirements.txt` installed in a virtual environment.
- `data/fetcher.py` pulls historical temperature data from Open-Meteo.
- `data/cleaner.py` handles basic missing values.
- `data/loader.py` returns a clean DataFrame.
- `notebooks/01_data_exploration.ipynb` visualizes distributions and spots anomalies.

**Definition of done**
You can fetch several years of daily temperature data for a city, clean it, and plot its distribution. Done.

**Still open**
- `data/loader.py` carries a leftover tutorial string at the top of the module. Delete it.

---

### Week 2, Baseline Model

**Deliverables**
- `models/baseline.py` uses historical mean and variance under a Gaussian assumption.
- Bucket probability is defined as P(a < T ≤ b) for each 1°C bucket, matching the Polymarket Hong Kong market structure.
- `notebooks/02_Baseline_Model.ipynb` fits the Gaussian, computes P(event), and visualizes it.
- `tests/test_data.py` validates the fetcher output schema.

**Definition of done**
Given a date, the baseline model returns a probability between 0 and 1. Done.

**Still open**
- `pricing/fair_value.py` maps a market titled `32°C` to the interval [32, 33). `decisions_log.md` describes the market as resolving on the rounded value, which would be [31.5, 32.5). One of the two is wrong. Pin it with a test against a known resolved market.

---

### Week 3, Bayesian + KDE Models

**Deliverables**
- `models/kde_model.py` fits a KDE and computes event probability via integration.
- `models/bayesian_model.py` turns a prior and a likelihood into a posterior update.
- `notebooks/03_KDE_Model.ipynb` fits the KDE, computes bucket probability, and compares it against the Gaussian baseline.
- `notebooks/04_Bayesian_Inference.ipynb` walks step by step through prior, likelihood, and posterior.
- `notebooks/05_Model_Comparison.ipynb` compares baseline, KDE, and Bayesian side by side.

**Definition of done**
Three models each return P(event). Bayesian outperforms both climatology only models on Brier and log loss. Done. See `decisions_log.md` Phase 1 Summary for the numbers.

**Still open**
- The Bayesian likelihood parameters (`mean_error`, `sigma_forecast`) are estimated in `models/bayesian_model.py` from the entire `df_pair` on every call. `df_pair` runs from `OOS_START` to yesterday, so each day's posterior is conditioned on that day's own realised forecast error and on future days. This is look ahead of the same kind that was already found and fixed for KDE. Fix is to estimate the two parameters once from a window strictly before the scoring window, or as an expanding window over rows with `date < day`, and pass them in rather than recomputing inside the model.
- `bayesian_interference` recomputes those same constants for every (day, bucket) pair, roughly 21k times per run. Compute once per run, the posterior once per day.
- `models/kde_model.py` refits `gaussian_kde` on the full history on every call. Fit once outside the lambda.

---

### Week 4, Evaluation + Calibration

**Deliverables**
- `evaluation/scoring.py` computes Brier score, log loss, and skill scores.
- `evaluation/calibration.py` builds reliability diagrams and calibration curves.
- Explicit IS/OOS split, implemented as `IS_START`/`IS_END`/`OOS_START`/`OOS_END` in `config/settings.py`. The split ended up IS = 2000-01-01 to 2016-12-31, OOS = 2017-01-01 to yesterday (dynamic). See `decisions_log.md` for the reasoning (Previous Runs API data availability, etc.).
- `notebooks/06_Calibration_Analysis.ipynb` runs the full calibration analysis of all three models on OOS data only.
- `tests/test_scoring.py` covers edge cases (p=0, p=1, perfect predictions).
- `tests/test_bayesian.py` checks the posterior sums to 1 and updates in the correct direction.

**Definition of done**
Reliability diagrams and calibration numbers reported per model in `notebooks/06_Calibration_Analysis.ipynb` and `decisions_log.md`. Done.

**Still open**
- `data/fetcher.py:fetch_previous_forecast_data` ignores its `start_date` and `end_date` arguments and always requests a hardcoded `past_days=1900` window ending today. `OOS_START` therefore has no effect on the forecast side, `df_pair` actually starts around mid 2021, and its start rolls forward one day per day.
- The same function does not pass `timezone=settings.TIMEZONE`, so hourly times come back in GMT and `get_daily_max` groups by UTC day while actuals use Hong Kong local days. The forecast daily max may be taken over the wrong 24 hour window.
- `tests/test_bayesian.py` has its `monkeypatch` lines commented out, so it hits live Open-Meteo. That is why the suite takes 17 seconds and fails offline.
- `data/cleaner.py` compares rows dropped after `interpolate()` rather than the longest run of consecutive nulls, so interior gaps of any length are linearly filled and pass.

---

### Week 5, Consolidation + run_experiment.py

**Deliverables**
- `run_experiment.py` runs the full Phase 1 pipeline end to end from config, and since Week 9 also runs Phase 2/3.
- All Phase 1 tests passing via `python3 -m pytest tests/`.
- Notebooks `01` to `08` are clean, run top to bottom, and saved with outputs so plots render on GitHub (rerun 2026-09-12).
- Phase 1 summary in `decisions_log.md`.

**Definition of done**
Someone clones the repo, runs `python3 run_experiment.py`, and gets calibration results, and now the full Phase 2/3 backtest and risk results too. Done, with the test command caveat under Week 9.

**Still open**
- `run_experiment.py` calls `fetch_all_data()` in `run_experiment()` and again inside `run_system()`, so every Open-Meteo request is issued twice and the first result is discarded.
- `USE_SYNTHECTIC_DATA` was committed as `True` until 2026-09-12 (now `False`). The name is also a typo, the flag should read `USE_SYNTHETIC_DATA`.

---

## Phase 2, Compare to the Market (Weeks 6–7)
The goal is to bring in Polymarket, detect mispricing, and size positions.

---

### Week 6, Polymarket Integration + Pricing

**Deliverables**
- `data/fetcher.py` extended to pull Polymarket market odds and price history for matching events.
- `pricing/fair_value.py` turns model probability into a fair value price.
- `pricing/edge.py` computes edge = P_model - P_market.
- `notebooks/07_Full_Backtest.ipynb` plots the edge distribution per model. This landed in `07` rather than `08`, since `08` ended up focused on Kelly and risk.

**Definition of done**
For a given date, you can compute edge between your model and Polymarket. Done.

**Still open**
- `data/fetcher.py` still contains a 55 line triple quoted block holding the old slug based `fetch_polymarket_data` implementation, and a dead `get_spread_polymarket` that targets the shut down Dome API with debug prints. Both should be deleted, git history keeps them.
- `fetch_all_price_history` fires one request per token id with 15 workers, no retry, no cache. Persist `df_result` to parquet and only fetch tokens not already cached, closed markets never change. See the caching item under Week 10.
- The request, error check, and DataFrame boilerplate is repeated six times across the fetchers. One private helper would do.

---

### Week 7, Risk Management

**Deliverables**
- `risk/kelly.py` implements the Kelly criterion and fractional Kelly. Kelly is deliberately two sided, negative f* signals betting the No side, not "don't bet." See `decisions_log.md`.
- `risk/metrics.py` computes VaR, Expected Shortfall, rolling max drawdown, and Sharpe ratio.
- Transaction costs are wired in. `config/settings.py:FEE_RATE` is deducted from realised P&L in `backtest/engine.py`. Spread only gates eligibility via `effective_edge_flag` and is never subtracted from a trade's realised payoff. See `decisions_log.md` for why.
- `pricing/edge.py` computes both gross edge and effective_edge (after spread and fees).
- `tests/test_kelly.py` checks that f* stays bounded for extreme inputs, that its sign matches the model vs market direction, and that fractional scaling is applied.
- `notebooks/08_Risk_Analysis_Kelly.ipynb` covers Kelly sizing plus the sensitivity analysis, f* vs. edge at fixed market odds, f* vs. market odds at fixed model probability, and a combined heatmap over the observed range of both.

**Definition of done**
Given an edge and spread, the system computes effective_edge and only sizes a position when effective_edge_flag clears both thresholds, and notebook 08 shows how f* changes with edge and odds. Done.

**Still open**
- `pricing/edge.py:effective_edge` subtracts spread/2 and FEE_RATE from the signed edge and then applies `abs()`. Verified 2026-09-12. Edge +0.06 is rejected (0.015 below `MIN_EFFECTIVE_EDGE`), edge -0.06 is accepted (-0.105). Every No side trade passes a looser filter than every Yes side trade. `tests/test_edge.py` misses it because its negative case already fails `MIN_EDGE`. Add a symmetric positive and negative case.
- Spread is a bare `0.05` literal inside `effective_edge` rather than a `settings` constant, so notebooks and tests cannot vary it.
- `sharpe_ratio` is `mean(profit) / std(profit)` over per trade rows. No time basis, no annualisation, no risk free rate. It is a per bet ratio, not a conventional Sharpe. Either document it as such in the README or compute it on daily P&L.
- `risk/metrics.py` imports `pandas` and `matplotlib.pyplot` unused, which breaks the no plotting in `.py` modules rule.

---

## Phase 3, Full System (Weeks 8–9)
The goal is an end to end backtest, with optional live execution.

---

### Week 8, Backtest Engine

**Deliverables**
- `backtest/engine.py` has a walk forward loop that is built and tested.
- `backtest/pnl.py` handles P&L tracking with transaction costs (fee only, see Week 7), max drawdown, and Sharpe via `run_all_models`/`get_pnl`.
- `notebooks/07_Full_Backtest.ipynb` has the full backtest pipeline built and run.
- Polymarket data constraint documented in `docs/data_sources.md`.

**Definition of done**
The system simulates historical decisions and produces a P&L series (`profit`/`cumulative_profit`) with VaR, Expected Shortfall, max drawdown, and Sharpe, per model, side by side. Done.

**How IS/OOS applies here**
The models are fit on `IS_START` to `IS_END` weather data. Every trade the engine sees comes from Polymarket, whose history only exists inside the OOS window, so trade dates are out of sample by default and there is no in sample slice of trades to split out. The exception is the Bayesian likelihood fit described under Week 3, which uses the scored days themselves. Until that is fixed the Bayesian backtest numbers carry a look ahead dependency.

**Still open**
- The result is one combined number per model over the whole Polymarket date range. A time split within that range (early vs. late) has not been done and would show whether the edge is stable over time.
- `evaluation/eval_loop.py:run_eval_loop_polymarket` takes a `prob_fn_factory` argument that has no effect on its output, the probability matrix it builds is never used. `df_res_gauss`, `df_res_kde`, and `df_res_bayes` in notebooks 07 and 08 are identical.
- The win/loss flag in `evaluation/eval_loop.py` is `when(correct == predicted).then(1).otherwise(0)`. Rows where either index is null (open ended buckets, or days whose actual falls outside 25 to 36°C) become a guaranteed loss for Yes and a free win for No. Derive ground truth from the market's own interval and leave the flag null when the actual is unknown.
- Kelly f* is computed independently per (date, bucket) row and summed against a fixed unit bankroll. No compounding, no cap, no aggregation of the up to 11 mutually exclusive bets on the same day.
- `backtest/pnl.py:get_pnl` prints from a library module instead of returning a dict, so results cannot be asserted in a test or tabulated in a notebook.

---

### Week 9, Polish + Documentation

**Deliverables**
- `README.md` updated with project description, how to run, results summary, and seven plots from the notebooks.
- `LICENSE` added (MIT).
- Notebooks `07` and `08` cleaned on 2026-09-11 (one import cell, dead cells removed, all text in English). All eight notebooks rerun and saved with outputs on 2026-09-12.
- All tests passing, 40 passed, via `python3 -m pytest tests/`.
- `decisions_log.md` updated through Phase 2/3.
- `run_experiment.py` covers the full pipeline, Phase 1 (scoring and calibration) and Phase 2/3 (edge, Kelly, backtest, risk) in one script.

**Definition of done**
Reproducible, tested, and documented end to end. `python3 run_experiment.py` runs the full pipeline and the test suite passes. Done, with the caveats below.

**Still open**
- Plain `pytest tests/` fails at collection with `ModuleNotFoundError` because there is no `conftest.py` and no `tests/__init__.py`. Only the `-m` form puts the repo root on `sys.path`. Add a `conftest.py` at the repo root, then the README can say `pytest tests/` again.
- `README.md` still lists `metrics.py` as VaR, Expected Shortfall, and drawdown in the module map. Sharpe lives there too.
- `docs/decisions_log.md` says the prior was built to 2015-01-01. `config/settings.py` says `IS_END = 2016-12-31`. One of them is stale.
- `docs/project_structure.md` lists `.env` for API keys and `python-dotenv` in requirements. Nothing reads any env var. Remove or correct.

---

## Week 10, Buffer and Open Items

Everything not yet closed, in the order it is worth doing before showing the repo around.

**Delete first**
- Tutorial string at the top of `data/loader.py`.
- The 55 line commented out block and `get_spread_polymarket` in `data/fetcher.py`.
- `config/config.yaml` and the `pyyaml` requirement.
- Unused imports in `risk/metrics.py`, `pricing/fair_value.py`, `evaluation/eval_loop.py`, and `run_experiment.py`.

**Correctness**
- `effective_edge` sign asymmetry (Week 7).
- Bayesian look ahead in the likelihood fit (Week 3).
- Win/loss flag defaulting null to 0 (Week 8).
- `fetch_previous_forecast_data` ignoring its date arguments and timezone (Week 4).
- Bucket interval vs. market rounding rule (Week 2).

**Reproducibility**
- `conftest.py` so `pytest tests/` works as documented (Week 9).
- Double `fetch_all_data()` call in `run_experiment.py` (Week 5).
- `tests/test_bayesian.py` hitting the live API (Week 4).
- Rename `USE_SYNTHECTIC_DATA` to `USE_SYNTHETIC_DATA` (Week 5).

**Analysis depth**
- Early vs. late time split of the backtest window (Week 8).
- Sharpe on daily P&L, or document the per bet definition (Week 7).
- Per day Kelly aggregation and a bankroll simulation (Week 8).

**Later**
- Live "what to bet on today" recommendation loop. Reuse the existing model probability, edge, effective_edge, and Kelly pipeline, but point it at currently open Polymarket markets (`closed == False`) instead of resolved ones, comparing today's model probability against today's live price. No ground truth step is needed since the outcome is not yet known. Wrap it in a simple `while True: run(); time.sleep(N)` loop in `execution/loop.py` (currently empty), no server, just a long running local process. Keep the interval conservative (15 to 30 minutes) given the Polymarket and Open-Meteo rate limits hit during development.
- Cache fetched Polymarket data to parquet instead of refetching on every run (Week 6).
- Real per market spread, if a viable source ever appears. This is a settled, permanent flat assumption decision, not an open search. See `decisions_log.md`.
