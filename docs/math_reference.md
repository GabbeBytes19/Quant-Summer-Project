# Math Reference

Key formulas used in the system. This is the source of truth — implement exactly these.
### Should be written in LateX, but that goes later
---

## Probability & Events

### Bucket Probability (from distribution)
```
P(a < X ≤ b) = ∫_a^b f(x) dx
```
In practice: `CDF(b) - CDF(a)` for parametric models, numerical integration for KDE.

Used to match Polymarket bucket structure — each 1°C bucket (e.g. "32°C" = [31.5, 32.5)) is a binary YES/NO contract.

### Gaussian bucket probability
```
P(a < X ≤ b) = Φ((b - μ) / σ) - Φ((a - μ) / σ)
```
where Φ is the standard normal CDF, μ = historical mean, σ = historical std.

---

## Bayesian Inference

### Bayes' Theorem
```
P(θ | D) = P(D | θ) · P(θ) / P(D)
```
- P(θ) = prior belief
- P(D | θ) = likelihood of data given θ
- P(D) = marginal likelihood (normalizing constant)
- P(θ | D) = posterior (updated belief)

### Sequential updating
```
P(θ | D₁, D₂) = P(D₂ | θ) · P(θ | D₁) / P(D₂)
```
Each new observation updates the posterior, which becomes the new prior.

---

## Kernel Density Estimation (KDE)

### KDE density estimate
```
f̂(x) = (1 / n·h) · Σᵢ K((x - xᵢ) / h)
```
- n = number of data points
- h = bandwidth (controls smoothness)
- K = kernel function (use Gaussian kernel by default)

### Gaussian kernel
```
K(u) = (1 / √(2π)) · exp(-u² / 2)
```

### Bandwidth selection
Use Silverman's rule of thumb as default:
```
h = 1.06 · σ · n^(-1/5)
```

---

## Evaluation — Proper Scoring Rules

### Brier Score
```
BS = (1/N) · Σₜ (fₜ - oₜ)²
```
- fₜ = predicted probability at time t
- oₜ = actual outcome (0 or 1)
- Range: [0, 1] — lower is better
- Perfect model: BS = 0, random model (f=0.5 always): BS = 0.25

### Log Loss (Binary Cross-Entropy)
```
LL = -(1/N) · Σₜ [oₜ · log(fₜ) + (1 - oₜ) · log(1 - fₜ)]
```
- Lower is better
- Penalizes confident wrong predictions heavily (log(0) → ∞)
- Clip predictions: fₜ ∈ [ε, 1-ε] to avoid numerical issues

### Brier Skill Score (relative to baseline)
```
BSS = 1 - BS_model / BS_baseline
```
- BSS > 0 means model beats baseline
- BSS = 1 means perfect model

### Expected Calibration Error (ECE)
```
ECE = Σ(m=1 to M) (|Bm| / N) · |ō_m - f̄_m|
```
- M = number of bins (typically 10, equal-width over [0,1])
- Bm = set of samples whose predicted probability falls in bin m
- |Bm| = count of samples in bin m
- N = total number of samples
- ō_m = observed frequency in bin m (fraction of events that actually occurred)
- f̄_m = mean predicted probability in bin m
- Range: [0, 1] — lower is better. ECE = 0 means perfect calibration.

**How to use:** Plot ō_m vs f̄_m (reliability diagram). ECE quantifies the area between that curve and the diagonal. Use alongside Brier score — a model can have low Brier score but poor calibration.

---

## Mispricing & Edge

### Edge (gross)
```
edge = P_model(event) - P_market(event)
```
- Positive edge: model thinks event more likely than market → consider buying
- Negative edge: model thinks event less likely than market → consider selling
- Only act when |edge| > minimum_edge threshold (e.g. 0.05)

### Effective Edge (after transaction costs)
```
effective_edge = edge - spread/2 - fee_rate
```
- spread = ask_price - bid_price (bid/ask spread on Polymarket)
- fee_rate = platform fee (Polymarket charges ~2%)
- **Only act when effective_edge > 0.** If edge = 2% but spread = 3%, the trade loses money regardless of what Kelly says.

### Transaction cost in P&L
```
net_pnl = gross_pnl - (stake × fee_rate) - (stake × spread/2)
```

### Market-implied probability (from decimal odds)
```
P_market = 1 / decimal_odds
```
Note: raw market odds include the overround (vig). Adjust:
```
P_market_adjusted = P_market / (P_buy + P_sell)
```

---

## Risk Management

### Kelly Criterion
```
f* = (b·p - q) / b
```
where:
- b = net decimal odds (e.g. b=2 means win 2x stake)
- p = P_model(event) = probability of winning
- q = 1 - p = probability of losing
- f* = fraction of bankroll to stake

Simplified form (when b = 1, i.e. even odds):
```
f* = p - q = 2p - 1
```

Edge form:
```
f* = edge / b
```

**Constraint:** f* must be clamped to [0, 1]. If f* < 0, do not bet.

### Fractional Kelly
```
f = κ · f*    where κ ∈ (0, 1)
```
Typical values: κ = 0.25 (quarter Kelly) for conservative sizing.
Reduces variance at the cost of slightly lower expected growth.

### Value at Risk (VaR)
```
VaR_α = -inf{x : P(L ≤ x) > α}
```
The loss not exceeded with probability α (e.g. α=0.95 → 95% VaR).
In practice: the α-th percentile of the loss distribution.

### Expected Shortfall (CVaR)
```
ES_α = E[L | L > VaR_α]
```
Average loss in the worst (1-α) fraction of scenarios.
More informative than VaR — captures tail risk.

### Maximum Drawdown
```
MDD = max_{t ∈ [0,T]} (peak_t - trough_t) / peak_t
```
The largest peak-to-trough decline in portfolio value as a fraction of peak.

---

## Expected Value

### Expected value of a bet
```
EV = p · b - (1 - p) · 1
   = p · (b + 1) - 1
```
where b = net odds, stake = 1 unit. Act only when EV > 0.

---

## Calibration

A model is perfectly calibrated if:
```
For all p: P(event | f = p) = p
```
i.e. among all predictions of 70%, the event occurs 70% of the time.

**Reliability diagram:** plot mean predicted probability (x-axis) vs observed frequency (y-axis). Perfect calibration = diagonal line.

**Summary metric:** use ECE (see above) to reduce the reliability diagram to a single number.

---

## Look-Ahead Bias

> This is the most common reason student quant projects fail interviews.

A model at time t must only use information available at time t.

**Wrong:** train on actual observed temperature on day t, then predict day t+1.
**Right:** train on forecast issued at time t for day t+1, then verify against actual outcome.

```
prediction(t) = f(data available at time t)
outcome(t)    = realized value at time t  ← only used for scoring, never for training
```

**In walk-forward validation:**
```
for each date t:
    train model on data[:t]          # everything strictly before t
    predict P(event at t+horizon)    # using only info available at t
    score against actual outcome[t]  # after the fact
```

Never let future outcomes leak into the training window.
