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

### Decision: Binary event formulation (P(T > threshold))
- **Alternatives considered:** regression (predict exact temperature), multi-class (cold/warm/hot)
- **Reason:** Binary events map directly to prediction market contracts (YES/NO). Allows use of proper scoring rules (Brier, log loss) and Kelly criterion. Simpler to calibrate and explain.
- **Date:** 2026-06-28

### Decision: Threshold set to 25°C
- **Alternatives considered:** 20°C, 30°C, seasonal adaptive threshold
- **Reason:** 25°C gives a balanced class distribution in summer months, avoiding degenerate base rates. Matches intuitive "warm day" definition. Can be adjusted via config.
- **Date:** 2026-06-28

### Decision: Strict Jupyter/module separation
- **Alternatives considered:** all logic in notebooks, all logic in .py files
- **Reason:** Notebooks for research thinking, .py modules for production logic. This is how real quant teams work. Mixing them makes the repo look like a student project.
- **Date:** 2026-06-28

### Decision: Use polar insead of pandas
- ** Polar should be used for dataset
- ** Reason: ** Polar are much faster, slepless integration without copying. 
- **Date:** 2026-06-29
## Models

*(Fill in as you make modeling decisions)*

---

## Evaluation

*(Fill in as you make evaluation decisions)*

---

## Risk

*(Fill in as you make risk management decisions)*
