# Project Roadmap

## Phase 1, Build the Brain (Weeks 1–5)
The goal is a working, calibrated probability model. No Polymarket yet.

---

### Week 1, Foundation
**Deliverables:**
- All folders and files scaffolded
- `config/settings.py` holds coordinates, date ranges, and the event threshold
- `config/config.yaml` was scaffolded here but nothing reads it, all real settings live in `config/settings.py` (see Week 10 cleanup)
- `.gitignore` covers `.env`, `__pycache__/`, `.ipynb_checkpoints/`, `.vscode/`, and `.DS_Store`. No API keys are needed anywhere in this project (Open-Meteo and Polymarket are both keyless), the `.env` entry is defensive.
- `requirements.txt` installed in virtual environment
- `data/fetcher.py` pulls historical temperature data from Open-Meteo
- `data/cleaner.py` handles basic missing values
- `data/loader.py` returns a clean DataFrame
- `notebooks/01_data_exploration.ipynb` visualizes distributions and spots anomalies

**Definition of done:** You can fetch 5 years of daily temperature data for a city, clean it, and plot its distribution.

---

### Week 2, Baseline Model
**Deliverables:**
- `models/baseline.py` uses historical mean/variance under a Gaussian assumption
- Bucket probability is defined as P(a < T ≤ b) for each 1°C bucket, matching Polymarket Hong Kong market structure
- `notebooks/02_Baseline_Model.ipynb` fits the Gaussian, computes P(event), and visualizes it
- `tests/test_data.py` validates the fetcher output schema

**Definition of done:** Given a date, baseline model returns a probability between 0 and 1.

---

### Week 3, Bayesian + KDE Models
**Deliverables:**
- `models/kde_model.py` fits KDE and computes event probability via integration
- `models/bayesian_model.py` turns a prior and likelihood into a posterior update
- `notebooks/03_KDE_Model.ipynb` fits KDE, computes bucket probability, and compares it against the Gaussian baseline
- `notebooks/04_Bayesian_Inference.ipynb` walks step by step through prior, likelihood, and posterior
- `notebooks/05_Model_Comparison.ipynb` compares baseline, KDE, and Bayesian side by side

**Definition of done:** Three models each return P(event). Bayesian outperforms both climatology only models on Brier/log loss. See `decisions_log.md` Phase 1 Summary for exact numbers and why.

---

### Week 4, Evaluation + Calibration
**Deliverables:**
- `evaluation/scoring.py` computes Brier score, log loss, and ECE
- `evaluation/calibration.py` builds reliability diagrams and calibration curves
- Explicit IS/OOS split, implemented as `IS_START`/`IS_END`/`OOS_START`/`OOS_END` in `config/settings.py`. Dates differ from the original plan (2015–2020/2021–2024). The actual split ended up IS = 2000-01-01 to 2016-12-31, OOS = 2017-01-01 to yesterday (dynamic). See `decisions_log.md` for the reasoning that landed on those dates (Previous Runs API data availability, etc.).
- `notebooks/06_Calibration_Analysis.ipynb` runs the full calibration analysis of all three models on OOS data only
- `tests/test_scoring.py` covers edge cases (p=0, p=1, perfect predictions)
- `tests/test_bayesian.py` checks the posterior sums to 1 and updates in the correct direction

**Definition of done:** Reliability diagrams and calibration numbers reported per model in `notebooks/06_Calibration_Analysis.ipynb` and `decisions_log.md`.

---

### Week 5, Consolidation + run_experiment.py
**Deliverables:**
- `run_experiment.py` runs the full Phase 1 pipeline end to end from config (now runs Phase 2/3 too, see Week 9)
- All Phase 1 tests passing (`PYTHONPATH=. pytest tests/`)
- Notebooks clean and readable. `07_Full_Backtest.ipynb` was cleaned up on 2026-09-11 (one import cell, dead cells removed, all text in English).
- Phase 1 summary in `decisions_log.md`

**Definition of done:** Someone clones the repo, runs `python3 run_experiment.py`, and gets calibration results (and now the full Phase 2/3 backtest/risk results too).

---

## Phase 2, Compare to the Market (Weeks 6–7)
The goal is to bring in Polymarket, detect mispricing, and size positions.

---

### Week 6, Polymarket Integration + Pricing
**Deliverables:**
- `data/fetcher.py` extended to pull Polymarket market odds for matching events
- `pricing/fair_value.py` turns model probability into a fair value price
- `pricing/edge.py` computes edge = P_model - P_market
- `notebooks/07_Full_Backtest.ipynb` plots edge over time (landed here instead of `08`, since `08` ended up focused purely on Kelly/risk numbers, see Week 7 note)

**Definition of done:** For a given date, you can compute edge between your model and Polymarket.

---

### Week 7, Risk Management
**Deliverables:**
- `risk/kelly.py` implements the Kelly criterion and fractional Kelly
- `risk/metrics.py` computes VaR, Expected Shortfall, and drawdown
- Transaction costs are wired in. `config/settings.py` → `FEE_RATE` is deducted from realized P&L in `backtest/engine.py`. Spread is not, it only gates eligibility via `effective_edge_flag` and is never subtracted from a trade's realized payoff. See `decisions_log.md` for why (spread has no real per market data source, and realized P&L only ever deducts the platform fee).
- `pricing/edge.py` computes both gross edge and effective_edge (after spread + fees)
- `tests/test_kelly.py` checks that f* stays bounded for extreme inputs, that its sign matches the model vs market direction, and that fractional scaling is applied. Note that "never < 0" from the original plan is no longer the right constraint. See `decisions_log.md`, Kelly is deliberately two sided now, negative f* signals betting the No side, not "don't bet."
- `notebooks/08_Risk_Analysis_Kelly.ipynb` covers Kelly sizing plus the sensitivity analysis, f* vs. edge at fixed market odds, f* vs. market odds at fixed model probability, and a combined heatmap over the observed range of both.

**Definition of done:** Given an edge and spread, system computes effective_edge and only sizes a position when effective_edge_flag clears both thresholds, and notebook 08 shows how f* changes with edge and odds. Done. One known bug in the filter itself is tracked in Week 10 (the sign asymmetry in `effective_edge`).

---

## Phase 3, Full System (Weeks 8–9)
The goal is an end to end backtest, with optional live execution.

---

### Week 8, Backtest Engine
**Deliverables:**
- `backtest/engine.py` has a walk forward loop that's built and tested. There is no IS/OOS check inside `engine()`. The models are fit on `IS_START` to `IS_END` weather data, and every trade the engine sees comes from Polymarket, whose history only exists inside the OOS window, so the trade dates are out of sample by default. The Bayesian likelihood fit is the exception, see Week 10.
- `backtest/pnl.py` handles P&L tracking with transaction costs (fee only, see Week 7 note), max drawdown, and Sharpe ratio via `run_all_models`/`get_pnl`. Sharpe is `mean(profit) / std(profit)` over per trade rows, not annualised, so it is a per bet ratio rather than a conventional Sharpe.
- `notebooks/07_Full_Backtest.ipynb` has the full backtest pipeline built and run here.
- Polymarket data constraint documented in `docs/data_sources.md`.

**Definition of done:** System simulates historical decisions and produces a P&L series (`profit`/`cumulative_profit`) with VaR/Expected Shortfall/max drawdown/Sharpe, per model, side by side. Done. The result is one combined number per model over the whole Polymarket date range, a time split within that range (early vs. late) has not been done.

---

### Week 9, Polish + Documentation
**Deliverables:**
- `README.md` updated with project description, how to run, and results summary
- All notebooks narratively complete. `07_Full_Backtest.ipynb` was cleaned up on 2026-09-11 (one import cell, dead cells removed, all text in English), and all eight notebooks were rerun and saved with outputs on 2026-09-12.
- All tests passing (`PYTHONPATH=. pytest tests/`, 40 passed)
- `decisions_log.md` fully updated
- `run_experiment.py` covers the full pipeline, extended this session to run Phase 1 (scoring/calibration) and Phase 2/3 (edge → Kelly → backtest → risk) end to end in one script.

**Definition of done:** Reproducible, tested, and documented end to end. `python3 run_experiment.py` runs the full pipeline and `PYTHONPATH=. pytest tests/` passes. One open item is that `notebook 07_Full_Backtest.ipynb` still has some scratch work cells (duplicated imports, a couple of disabled exploratory cells) left over from active development, tracked as a follow up narrative cleanup pass rather than a functional gap.

---

## Week 10, Buffer
For anything that slipped, extra experimentation, or extending models.

- **Live "what to bet on today" recommendation loop.** Reuse the existing model probability + edge/effective_edge/Kelly pipeline, but point it at currently open Polymarket markets (`closed == False`) instead of resolved ones, comparing today's model probability against today's live price. No ground truth/win loss step is needed (the outcome isn't known yet). Wrap it in a simple `while True: run(); time.sleep(N)` loop living in `execution/loop.py` (previously empty), no server/cloud hosting, just a long running local process. The interval should stay conservative (15-30 min) given this session's repeated experience with both Polymarket and Open-Meteo rate limits under rapid repeated requests.
- Sharpe ratio in `backtest/pnl.py` — done, see `risk/metrics.py:sharpe_ratio`.
- `notebooks/08_Risk_Analysis_Kelly.ipynb`, Kelly sensitivity analysis (f* vs. edge, f* vs. odds) — done.
- Real per market spread, if a viable source ever appears. See `decisions_log.md`, this is currently a settled, permanent flat assumption decision, not an open search.
- ~~IS/OOS split reported separately in the backtest~~ — not applicable. `IS_START`/`IS_END` only feeds the Phase 1 climatology fit; every backtested trade comes from Polymarket data, which only exists within the OOS window by construction. There's no in-sample slice of trades to split out. See `decisions_log.md` correction, 2026-09-11.
