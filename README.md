# Quant Summer Project

A probabilistic decision-making and pricing research platform — not a trading bot. It builds calibrated probability distributions over a real-world weather event (daily max temperature in Hong Kong), compares those model-implied probabilities against Polymarket's market-implied prices, and evaluates whether the resulting mispricing survives risk-adjusted position sizing and transaction costs.

The goal is **probabilistic accuracy and risk-adjusted decision quality** — not raw P&L. Every result in this repo should be read with that in mind.

## What it does

1. **Ingests data** — historical + forecast temperature data (Open-Meteo) and resolved prediction-market data (Polymarket).
2. **Builds probability models** — three independent estimators of P(temperature in bucket): a Gaussian baseline, a KDE model, and a Bayesian model that updates a climatological prior with the day's specific forecast.
3. **Scores the models** — Brier score, log loss, and calibration curves, out-of-sample.
4. **Prices the edge** — `edge = model_probability − market_probability`, filtered down to `effective_edge` after an assumed spread and Polymarket's platform fee.
5. **Sizes positions** — fractional Kelly criterion, based on each model's probability and the market's implied odds.
6. **Backtests it** — walk-forward simulation of buying whichever side (Yes/No) the edge favors, only when the edge clears both a raw and a fee-adjusted threshold.
7. **Measures risk** — Value at Risk, Expected Shortfall, and running drawdown on the resulting P&L series.

## Module map

| Module | Role |
|---|---|
| `data/` | Fetch, clean, and align weather + Polymarket data |
| `models/` | Gaussian baseline, KDE, Bayesian probability estimators |
| `pricing/` | `fair_value.py` (buckets, probability vectors), `edge.py` (model vs. market edge) |
| `risk/` | `kelly.py` (position sizing), `metrics.py` (VaR, Expected Shortfall, drawdown) |
| `backtest/` | `engine.py` (per-model walk-forward simulation) |
| `evaluation/` | `scoring.py`, `calibration.py`, `eval_loop.py` (ground-truth matching) |
| `notebooks/` | All exploration, math, and plots — see `notebooks/07_Full_Backtest.ipynb` for the end-to-end pipeline |

## How to run

```bash
pip install -r requirements.txt
```

**Full pipeline, one command:**

```bash
python3 run_experiment.py
```

This runs everything end-to-end: fetches weather + Polymarket data, fits all three probability models, prints Brier score/log loss/skill scores/calibration tables (Phase 1), then computes ground truth once, builds each model's probability vector, computes edge/effective_edge, runs the backtest per model via `backtest.engine.engine`, and prints profit/VaR/Expected Shortfall/max drawdown/trade count per model via `backtest.pnl.get_pnl` (Phase 2/3). No notebook required.

Set `USE_SYNTHECTIC_DATA = True` in `config/settings.py` to swap the weather-actuals fetch for fast, offline synthetic data during development — note this only covers the weather side, Polymarket fetching always hits the live API regardless.

The same pipeline is also explorable step-by-step in `notebooks/07_Full_Backtest.ipynb`.

**Tests:**

```bash
pytest tests/
```

## Results summary (illustrative — see limitations on reproducibility)

- **Model comparison**: the Bayesian model clearly outperforms the Gaussian and KDE baselines on both proper scoring rules — Brier score ≈ 0.77–0.90 vs. ≈ 0.90–1.03 depending on the run, and a similar gap in log loss.
- **Calibration**: all three models are reasonably calibrated across probability buckets on out-of-sample data; the Bayesian model's calibration is checked bucket-by-bucket against realized outcomes in `notebooks/06_Calibration_Analysis.ipynb`.
- **Backtest**: this tracks through cleanly into the backtest — in every run so far, Bayesian has ended with the highest cumulative profit *and* the lowest VaR, Expected Shortfall, and max drawdown of the three models. One representative run: Bayesian profit 85.2 / VaR 0.096 / Expected Shortfall 0.146 / max drawdown 1.13, vs. Gaussian profit 39.2 / VaR 0.174 / Expected Shortfall 0.219 / max drawdown 2.43 (KDE landed close to Gaussian). Better-calibrated probabilities are translating into better risk-adjusted outcomes, not just better scores in isolation.

## Known limitations

- **Backtest results aren't perfectly reproducible run-to-run**, even at a matching total market count. Polymarket's dataset is live/unbounded and always growing, `settings.OOS_END` is defined as "yesterday" (shifts daily), and individual markets can update between runs — so treat specific numbers above as illustrative of the *pattern* (Bayesian wins on every axis), not as fixed values you should expect to reproduce exactly.
- **Spread is a flat assumed constant** (`spread = 0.05` in `pricing/edge.py:effective_edge()`), not real historical data — and this is a **permanent** decision, not a temporary gap. Polymarket's live order-book API only covers currently-open markets (every market here is already resolved). Checked and ruled out: Dome API (real, but Polymarket acquired and shut it down in April 2026), PolymarketData.co (paid/tiered), Bitquery (wrong kind of data — trades, not order books — also paid), pmxt (live-only, no historical support). Full L2 order-book history is expensive enough to store that every option either charges, expects self-hosted chain indexing, or doesn't have the real bid/ask at all. See `docs/decisions_log.md`.
- **No Sharpe ratio**, and IS/OOS results aren't reported *separately* in the backtest (one combined result per model) — both tracked as open items.
- `notebooks/08_Risk_Analysis_Kelly.ipynb` (Kelly sensitivity analysis, f* vs. edge/odds) is still empty.
- A live "what should I bet on today" recommendation loop (reusing this same pipeline against currently-open markets instead of resolved ones) is sketched but not yet built — see `docs/roadmap.md`, Week 10.

See `docs/decisions_log.md` and `docs/roadmap.md` for the full history and current status of every module.
