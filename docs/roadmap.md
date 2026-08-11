# Project Roadmap

## Phase 1 — Build the Brain (Weeks 1–5)
Goal: a working, calibrated probability model. No Polymarket yet.

---

### Week 1 — Foundation
**Deliverables:**
- [ ] All folders and files scaffolded
- [ ] `config/settings.py` — coordinates, date ranges, event threshold
- [ ] `config/config.yaml` — environment config
- [ ] `.gitignore` with `.env`
- [ ] `requirements.txt` installed in virtual environment
- [ ] `data/fetcher.py` — pull historical temperature data from Open-Meteo
- [ ] `data/cleaner.py` — basic missing value handling
- [ ] `data/loader.py` — return clean DataFrame
- [ ] `notebooks/01_data_exploration.ipynb` — visualize distributions, spot anomalies

**Definition of done:** You can fetch 5 years of daily temperature data for a city, clean it, and plot its distribution.

---

### Week 2 — Baseline Model
**Deliverables:**
- [ ] `models/baseline.py` — historical mean/variance, Gaussian assumption
- [ ] Bucket probability defined: e.g. P(a < T ≤ b) for each 1°C bucket, matching Polymarket Hong Kong market structure
- [ ] `notebooks/02_Baseline_Model.ipynb` — fit Gaussian, compute P(event), visualize
- [ ] `tests/test_data.py` — validate fetcher output schema

**Definition of done:** Given a date, baseline model returns a probability between 0 and 1.

---

### Week 3 — Bayesian + KDE Models
**Deliverables:**
- [ ] `models/kde_model.py` — KDE fit, event probability via integration
- [ ] `models/bayesian_model.py` — prior + likelihood → posterior update
- [ ] `notebooks/03_KDE_Model.ipynb` — KDE fit, bucket probability, compare vs Gaussian baseline
- [ ] `notebooks/04_Bayesian_Inference.ipynb` — step-by-step: prior, likelihood, posterior
- [ ] `notebooks/05_Model_Comparison.ipynb` — baseline vs KDE vs Bayesian side-by-side

**Definition of done:** Three models each return P(event). You can explain which fits better and why.

---

### Week 4 — Evaluation + Calibration
**Deliverables:**
- [ ] `evaluation/scoring.py` — Brier score, log loss, ECE
- [ ] `evaluation/calibration.py` — reliability diagrams, calibration curves
- [ ] Explicit IS/OOS split: 2015–2020 = In-Sample (training), 2021–2024 = Out-of-Sample (evaluation)
- [ ] `notebooks/06_Calibration_Analysis.ipynb` — full calibration analysis of all three models on OOS data only
- [ ] `tests/test_scoring.py` — edge cases (p=0, p=1, perfect predictions)
- [ ] `tests/test_bayesian.py` — posterior sums to 1, updates in correct direction

**Definition of done:** You can show a reliability diagram on OOS data and report ECE for each model. You can explain the IS/OOS split and why it prevents overfitting.

---

### Week 5 — Consolidation + run_experiment.py
**Deliverables:**
- [ ] `run_experiment.py` — runs full Phase 1 pipeline end-to-end from config
- [ ] All Phase 1 tests passing (`pytest tests/`)
- [ ] Notebooks clean and readable (output cells cleared, narrative complete)
- [ ] Phase 1 summary in `decisions_log.md`

**Definition of done:** Someone clones the repo, runs `python run_experiment.py`, and gets calibration results.

---

## Phase 2 — Compare to the Market (Weeks 6–7)
Goal: bring in Polymarket, detect mispricing, size positions.

---

### Week 6 — Polymarket Integration + Pricing
**Deliverables:**
- [x] `data/fetcher.py` extended — pull Polymarket market odds for matching events
- [x] `pricing/fair_value.py` — model probability → fair value price
- [x] `pricing/edge.py` — edge = P_model - P_market
- [x] `notebooks/07_Full_Backtest.ipynb` — plot edge over time *(landed here instead of `08`, since `08` ended up focused purely on Kelly/risk numbers — see Week 7 note)*

**Definition of done:** ✅ For a given date, you can compute edge between your model and Polymarket.

---

### Week 7 — Risk Management
**Deliverables:**
- [x] `risk/kelly.py` — Kelly criterion, fractional Kelly
- [x] `risk/metrics.py` — VaR, Expected Shortfall, drawdown
- [~] Transaction costs wired in: `config/settings.py` → `FEE_RATE` is deducted from realized P&L in `backtest/engine.py`; **spread is not** — it only gates *eligibility* via `effective_edge_flag`, it's never subtracted from a trade's realized payoff. See `decisions_log.md` for why (spread has no real per-market data source; realized P&L only ever deducts the platform fee).
- [x] `pricing/edge.py` — compute both gross edge and effective_edge (after spread + fees)
- [x] `tests/test_kelly.py` — f* stays bounded for extreme inputs, sign matches model-vs-market direction, fractional scaling applied. *(Note: "never < 0" from the original plan is no longer the right constraint — see `decisions_log.md`, Kelly is deliberately two-sided now: negative f* signals betting the No side, not "don't bet.")*
- [ ] `notebooks/08_Risk_Analysis_Kelly.ipynb` — Kelly sizing + sensitivity analysis — **not built**; Kelly/risk numbers currently only surface via `backtest/pnl.py:get_pnl()`'s printed summary, not a dedicated notebook. Still open.

**Definition of done:** ✅ Given an edge and spread, system computes effective_edge and only sizes a position when effective_edge_flag clears both thresholds. ⚠️ The "show how f* changes with edge and odds" sensitivity-analysis half is not done.

---

## Phase 3 — Full System (Weeks 8–9)
Goal: end-to-end backtest, optional live execution.

---

### Week 8 — Backtest Engine
**Deliverables:**
- [~] `backtest/engine.py` — walk-forward loop built and tested; IS/OOS boundary is enforced *upstream* (via `settings.OOS_START`/`OOS_END` bounding what data reaches the engine), not as an explicit check inside `engine()` itself.
- [~] `backtest/pnl.py` — P&L tracking with transaction costs (fee only, see Week 7 note) and max drawdown are done via `run_all_models`/`get_pnl`. **No Sharpe ratio** — not built.
- [~] `notebooks/07_Full_Backtest.ipynb` — full backtest pipeline built and run here; IS/OOS periods are **not** explicitly labeled on plots.
- [x] Polymarket data constraint — documented in `docs/data_sources.md`.

**Definition of done:** ✅ System simulates historical decisions and produces a P&L series (`profit`/`cumulative_profit`) with VaR/Expected Shortfall/max drawdown, per model, side by side. ⚠️ IS/OOS results are not reported *separately* — the backtest currently reports one combined result per model, not split by IS/OOS.

---

### Week 9 — Polish + Documentation
**Deliverables:**
- [x] README.md updated — project description, how to run, results summary
- [ ] All notebooks narratively complete — `07_Full_Backtest.ipynb` still has commented-out exploratory cells; not yet a clean, readable research report.
- [x] All tests passing (`pytest tests/` — 37 passed)
- [x] `decisions_log.md` fully updated
- [x] `run_experiment.py` covers full pipeline — extended this session to run Phase 1 (scoring/calibration) *and* Phase 2/3 (edge → Kelly → backtest → risk) end-to-end in one script.

**Definition of done:** Mostly there — reproducible, tested, documented end-to-end. Not fully "interview-ready in 10 minutes" yet, since notebook 07 itself is still a working scratchpad rather than a clean narrative.

---

## Week 10 — Buffer
For anything that slipped, extra experimentation, or extending models.

- [ ] **Live "what to bet on today" recommendation loop** — reuse the existing model-probability + edge/effective_edge/Kelly pipeline, but pointed at *currently open* Polymarket markets (`closed == False`) instead of resolved ones, comparing today's model probability against today's live price. No ground-truth/win-loss step needed (outcome isn't known yet). Wrap in a simple `while True: run(); time.sleep(N)` loop living in `execution/loop.py` (previously empty) — no server/cloud hosting, just a long-running local process. Interval should stay conservative (15-30 min) given this session's repeated experience with both Polymarket and Open-Meteo rate limits under rapid repeated requests.
- [ ] Sharpe ratio in `backtest/pnl.py`
- [ ] `notebooks/08_Risk_Analysis_Kelly.ipynb` — Kelly sensitivity analysis (f* vs. edge, f* vs. odds)
- [ ] Real per-market spread, if a viable source ever appears — see `decisions_log.md`; currently a settled, permanent flat-assumption decision, not an open search.
- [ ] IS/OOS split reported separately in the backtest (currently one combined result per model)
