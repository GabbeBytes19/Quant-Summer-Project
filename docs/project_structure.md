# Project Structure

## Repo root: `Quant-Summer-Project/`

```
Quant-Summer-Project/
│
├── data/
│   ├── __init__.py
│   ├── fetcher.py          # Open-Meteo API calls — pull historical + forecast weather
│   ├── cleaner.py          # handle missing values, outliers, time alignment
│   └── loader.py           # load cleaned data into standard DataFrame format
│
├── models/
│   ├── __init__.py
│   ├── baseline.py         # historical mean/variance model (simplest benchmark)
│   ├── kde_model.py        # Kernel Density Estimation model
│   └── bayesian_model.py   # Bayesian updating of beliefs
│
├── pricing/
│   ├── __init__.py
│   ├── fair_value.py       # probability → implied fair value
│   └── edge.py             # edge = model_probability - market_probability
│
├── risk/
│   ├── __init__.py
│   ├── kelly.py            # Kelly criterion + fractional Kelly sizing
│   └── metrics.py          # VaR, Expected Shortfall, drawdown constraints
│
├── backtest/
│   ├── __init__.py
│   ├── engine.py           # per-model backtest: filter by effective_edge_flag, decide side, size via Kelly, compute profit/cumulative_profit
│   └── pnl.py              # run_all_models() loops engine() across models; get_pnl() prints profit/VaR/Expected Shortfall/max drawdown/trade count per model
│
├── evaluation/
│   ├── __init__.py
│   ├── scoring.py          # Brier score, log loss
│   └── calibration.py      # calibration curves, reliability diagrams
│
├── execution/              # Phase 3 / Week 10 buffer
│   ├── __init__.py
│   └── loop.py             # planned: `while True: run(); sleep(N)` loop for a live "what to bet on today" recommendation against currently-open markets — not yet built, see roadmap.md Week 10
│
├── tests/
│   ├── fixtures/
│   │   └── synthetic_data.py   # fake Open-Meteo responses (same schema as real API) — avoids rate limits during dev
│   ├── test_kelly.py       # sign/bounds of f*, fractional scaling applied
│   ├── test_scoring.py     # Brier/log-loss edge cases
│   ├── test_bayesian.py    # posterior sums to 1, updates correctly
│   ├── test_data.py        # fetcher returns expected schema
│   ├── test_fair_value.py  # bucket parsing, open-ended buckets, probability vector building
│   ├── test_edge.py        # prob_market_v_model doesn't mutate input; effective_edge_flag requires both thresholds
│   ├── test_engine.py      # excludes price_paid==0/1; win/loss logic; cumulative_profit is a true running total
│   ├── test_eval_loop.py   # open-ended buckets get None; ground truth matches by date, not row position
│   └── test_metrics.py     # drawdown never negative; VaR/Expected Shortfall match manual calculation
│
├── config/
│   ├── settings.py         # global constants (coordinates, timeframes, thresholds)
│   └── config.yaml         # environment-specific configuration
│
├── notebooks/
│   ├── 01_data_exploration.ipynb       # Phase 1 — explore raw weather data
│   ├── 02_Baseline_Model.ipynb         # Phase 1 — fit baseline, compute P(event)
│   ├── 03_KDE_Model.ipynb              # Phase 1 — KDE fit, bucket probability, compare vs Gaussian baseline
│   ├── 04_Bayesian_Inference.ipynb     # Phase 1 — step-by-step Bayesian update
│   ├── 05_Model_Comparison.ipynb       # Phase 1 — baseline vs KDE vs Bayesian
│   ├── 06_Calibration_Analysis.ipynb   # Phase 1 — Brier, log loss, reliability diagrams
│   ├── 07_Full_Backtest.ipynb          # Phase 2/3 — full system simulation
│   └── 08_Risk_Analysis_Kelly.ipynb    # Phase 2 — Kelly sizing, drawdown analysis
│
├── run_experiment.py       # top-level reproducibility script — runs full pipeline
├── .env                    # API keys (gitignored)
├── .gitignore
└── requirements.txt
```

## Requirements

```
numpy
polars
scipy
matplotlib
seaborn
jupyter
requests
scikit-learn
statsmodels
pytest
pyyaml
python-dotenv
```

## Phase build order

| Phase | Modules active | Goal |
|-------|---------------|------|
| 1 | `data/`, `models/`, `evaluation/`, `tests/` | Build + calibrate the probability model |
| 2 | + `pricing/`, `risk/` | Compare to Polymarket, detect mispricing, size positions |
| 3 | + `backtest/`, `execution/` | Full simulation + (optional) live execution |
