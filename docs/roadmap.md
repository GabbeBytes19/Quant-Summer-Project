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
- [ ] `notebooks/06_Model_Comparison.ipynb` — baseline vs KDE vs Bayesian side-by-side

**Definition of done:** Three models each return P(event). You can explain which fits better and why.

---

### Week 4 — Evaluation + Calibration
**Deliverables:**
- [ ] `evaluation/scoring.py` — Brier score, log loss, ECE
- [ ] `evaluation/calibration.py` — reliability diagrams, calibration curves
- [ ] Explicit IS/OOS split: 2015–2020 = In-Sample (training), 2021–2024 = Out-of-Sample (evaluation)
- [ ] `notebooks/05_Calibration_Analysis.ipynb` — full calibration analysis of all three models on OOS data only
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
- [ ] `data/fetcher.py` extended — pull Polymarket market odds for matching events
- [ ] `pricing/fair_value.py` — model probability → fair value price
- [ ] `pricing/edge.py` — edge = P_model - P_market
- [ ] `notebooks/08_Risk_Analysis_Kelly.ipynb` (partial) — plot edge over time

**Definition of done:** For a given date, you can compute edge between your model and Polymarket.

---

### Week 7 — Risk Management
**Deliverables:**
- [ ] `risk/kelly.py` — Kelly criterion, fractional Kelly
- [ ] `risk/metrics.py` — VaR, Expected Shortfall, drawdown
- [ ] Transaction costs wired in: `config/settings.py` → `FEE_RATE`, spread deducted in `backtest/pnl.py`
- [ ] `pricing/edge.py` — compute both gross edge and effective_edge (after spread + fees)
- [ ] `tests/test_kelly.py` — f* never > 1.0 or < 0, behaves correctly at edge=0, returns 0 when effective_edge ≤ 0
- [ ] `notebooks/08_Risk_Analysis_Kelly.ipynb` (complete) — Kelly sizing + sensitivity analysis, show how spread kills thin-edge trades

**Definition of done:** Given an edge and spread, system computes effective_edge and only sizes a position when effective_edge > 0. You can show how f* changes with edge and odds.

---

## Phase 3 — Full System (Weeks 8–9)
Goal: end-to-end backtest, optional live execution.

---

### Week 8 — Backtest Engine
**Deliverables:**
- [ ] `backtest/engine.py` — walk-forward loop, strict IS/OOS boundary enforced in code
- [ ] `backtest/pnl.py` — P&L tracking with transaction costs deducted, Sharpe ratio, max drawdown
- [ ] `notebooks/07_Full_Backtest.ipynb` — run full backtest; clearly label IS vs OOS periods on all plots
- [ ] Note Polymarket data constraint in notebook: Phase 2 edge backtest limited to ~2024 onwards

**Definition of done:** System simulates historical decisions and produces a P&L curve with statistics. IS and OOS results are reported separately. Transaction costs are visible in the P&L breakdown.

---

### Week 9 — Polish + Documentation
**Deliverables:**
- [ ] README.md updated — project description, how to run, results summary
- [ ] All notebooks narratively complete (readable as a research report)
- [ ] All tests passing
- [ ] `decisions_log.md` fully updated
- [ ] `run_experiment.py` covers full pipeline

**Definition of done:** The repo is interview-ready. You can walk someone through it in 10 minutes.

---

## Week 10 — Buffer
For anything that slipped, extra experimentation, or extending models.
