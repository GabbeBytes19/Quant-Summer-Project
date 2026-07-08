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

### Decision: Bucket probability formulation (P(a < T ≤ b))
- **Alternatives considered:** binary threshold (P(T > threshold)), regression (predict exact temperature)
- **Reason:** Polymarket Hong Kong temperature markets resolve to 1°C buckets (e.g. "32°C" means the high fell in [31.5, 32.5)). Matching the market structure exactly allows direct comparison of model probabilities to market-implied probabilities. Each bucket is still a binary YES/NO contract — proper scoring rules (Brier, log loss) and Kelly criterion still apply.
- **Date:** 2026-07-08

### Decision: City changed to Hong Kong, threshold 30°C
- **Alternatives considered:** Linköping (25°C threshold), Seoul
- **Reason:** Hong Kong has active Polymarket daily temperature markets. Linköping does not. 30°C is a natural midpoint in the Hong Kong market's bucket range (25°C–35°C+) and aligns with the subtropical summer climate. Hong Kong summer temperatures also fit a Gaussian well, making the baseline model more meaningful.
- **Date:** 2026-07-08

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
