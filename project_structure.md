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
│   ├── engine.py           # walk-forward simulation loop
│   └── pnl.py              # P&L tracking and strategy statistics
│
├── evaluation/
│   ├── __init__.py
│   ├── scoring.py          # Brier score, log loss
│   └── calibration.py      # calibration curves, reliability diagrams
│
├── execution/              # Phase 3 only — leave empty for now
│   ├── __init__.py
│   └── loop.py             # async trading loop, order management
│
├── tests/
│   ├── test_kelly.py       # Kelly never returns f* > 1.0 or < 0
│   ├── test_scoring.py     # Brier/log-loss edge cases
│   ├── test_bayesian.py    # posterior sums to 1, updates correctly
│   └── test_data.py        # fetcher returns expected schema
│
├── config/
│   ├── settings.py         # global constants (coordinates, timeframes, thresholds)
│   └── config.yaml         # environment-specific configuration
│
├── notebooks/
│   ├── 01_data_exploration.ipynb       # Phase 1 — explore raw weather data
│   ├── 02_baseline_model.ipynb         # Phase 1 — fit baseline, compute P(event)
│   ├── 03_bayesian_inference.ipynb     # Phase 1 — step-by-step Bayesian update
│   ├── 04_model_comparison.ipynb       # Phase 1 — baseline vs KDE vs Bayesian
│   ├── 05_calibration_analysis.ipynb   # Phase 1 — Brier, log loss, reliability diagrams
│   ├── 06_risk_analysis_kelly.ipynb    # Phase 2 — Kelly sizing, drawdown analysis
│   └── 07_full_backtest.ipynb          # Phase 2/3 — full system simulation
│
├── run_experiment.py       # top-level reproducibility script — runs full pipeline
├── .env                    # API keys (gitignored)
├── .gitignore
└── requirements.txt
```

## Requirements

```
numpy
pandas
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
