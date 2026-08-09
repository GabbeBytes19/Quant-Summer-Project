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

**Phase 1 pipeline (model comparison + calibration only):**

```bash
python run_experiment.py
```

This fetches weather data, fits all three probability models, and prints Brier score, log loss, skill scores, and calibration tables. It does **not** yet cover the Phase 2/3 pipeline below — see "Known limitations."

**Full pipeline (edge → Kelly → backtest → risk):**

Currently lives in `notebooks/07_Full_Backtest.ipynb`, run top to bottom. It:
- builds the weather + Polymarket datasets,
- computes ground truth (`evaluation.eval_loop.run_eval_loop_polymarket`) once,
- computes each model's probability vector,
- computes edge (`pricing.edge.prob_market_v_model`, `effective_edge`),
- runs the backtest per model (`backtest.engine.engine`),
- computes VaR / Expected Shortfall / drawdown on each model's result (`risk.metrics`).

**Tests:**

```bash
pytest tests/
```

## Results summary (illustrative, not final — see limitations)

- **Model comparison**: the Bayesian model clearly outperforms the Gaussian and KDE baselines on both proper scoring rules — Brier score ≈ 0.744 vs. ≈ 0.885–0.889, and a similar gap in log loss. This tracks through the rest of the pipeline: the Bayesian backtest also ends with the highest cumulative profit of the three models.
- **Calibration**: all three models are reasonably calibrated across probability buckets on out-of-sample data; the Bayesian model's calibration is checked bucket-by-bucket against realized outcomes in `notebooks/06_Calibration_Analysis.ipynb`.
- **Edge distribution**: model vs. market edge is centered near zero for all three models (the market and the models mostly agree), with the Bayesian model showing a visible mass of larger positive-edge opportunities that the Gaussian/KDE models don't pick up — consistent with it being the better-calibrated model.
- **Backtest**: after filtering for markets that clear both the raw-edge and fee-adjusted-edge thresholds, all three models are net profitable over the sampled period, with Bayesian outperforming.

## Known limitations (deliberately placeholder, tracked as next steps)

- **Position sizing is currently a flat constant, not a real Kelly stake.** `risk.kelly.kelly_criterion` exists and is correct, but the backtest hasn't been wired to call it per-trade yet — every trade currently risks the same fixed amount regardless of the model's actual edge or the market's odds.
- **Spread is a flat assumed constant, not real historical data.** Polymarket's live order-book API only covers currently-open markets; every market in this backtest is already resolved, so there's no live order book left to query. Real historical spread would require a paid third-party API (checked: Dome API, PolymarketData.co — both gated behind signup). `settings.ASSUMED_SPREAD` is used as an explicit, documented stand-in.
- Because of the two points above, the VaR/Expected Shortfall numbers currently collapse to the flat stake value (every loss is identical in size), so they aren't yet measuring real tail risk — that becomes meaningful once real Kelly sizing is in place.
- `backtest/pnl.py` is scaffolded but empty — a natural home for a wrapper that runs all three models and collects results together, instead of calling `engine()` three times by hand.
- `run_experiment.py` only covers the Phase 1 (model comparison / calibration) pipeline — it hasn't been extended to run the edge / Kelly / backtest / risk pipeline yet.
