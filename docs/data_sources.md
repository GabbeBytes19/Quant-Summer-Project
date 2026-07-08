# Data Sources

---

## Phase 1 — Open-Meteo (Weather Data)

**URL:** https://open-meteo.com/  
**Cost:** Free, no API key required  
**Docs:** https://open-meteo.com/en/docs

### ⚠️ Look-Ahead Bias Warning
The archive endpoint returns **observed actuals** — what really happened. This is correct for scoring model predictions, but **must never be used as input features for training**. A model trained on actuals would implicitly "know the future."

For Phase 1, the safe approach is **walk-forward validation**: train only on data strictly before date t, predict for t, score against actuals at t. Never let actuals at t leak into the training window.

For more realistic simulation (Phase 2+), use the **historical forecast endpoint** which returns what NWP models predicted at time t — i.e. the information actually available at decision time.

### Historical actuals endpoint (for scoring only)
```
GET https://archive-api.open-meteo.com/v1/archive
```

### Key parameters
| Parameter | Value | Description |
|-----------|-------|-------------|
| `latitude` | e.g. 22.32 | City latitude |
| `longitude` | e.g. 114.17 | City longitude (Hong Kong example) |
| `start_date` | YYYY-MM-DD | Start of historical range |
| `end_date` | YYYY-MM-DD | End of historical range |
| `daily` | `temperature_2m_max` | Max daily temp at 2m height |
| `daily` | `temperature_2m_min` | Min daily temp |
| `daily` | `precipitation_sum` | Daily precipitation (mm) |
| `timezone` | `Asia/Hong_Kong` | Timezone for date alignment |

### Example request
```
https://archive-api.open-meteo.com/v1/archive
  ?latitude=22.32
  &longitude=114.17
  &start_date=2015-01-01
  &end_date=2024-12-31
  &daily=temperature_2m_max,temperature_2m_min,precipitation_sum
  &timezone=Asia%2FHong_Kong
```

### Response schema
```json
{
  "daily": {
    "time": ["2015-01-01", "2015-01-02", ...],
    "temperature_2m_max": [2.1, 3.4, ...],
    "temperature_2m_min": [-1.2, 0.5, ...],
    "precipitation_sum": [0.0, 2.3, ...]
  }
}
```

### Historical forecast endpoint (for training features — avoids look-ahead bias)
```
GET https://historical-forecast-api.open-meteo.com/v1/forecast
```
Returns what forecast models predicted at each past date — the information that was actually available. Use this as model input features to avoid look-ahead bias.

Same parameters as archive. Add `models=ecmwf_ifs04` or similar to specify the NWP model.

### Live forecast endpoint (for Phase 3)
```
GET https://api.open-meteo.com/v1/forecast
```
Returns 7–16 day forecast from current date. Use for Phase 3 live execution.

### Binary event definition (Phase 1)
```
event = 1  if temperature_2m_max > threshold  else  0
```
Recommended starting threshold: **30°C** (typical Hong Kong summer day).
This gives a roughly balanced class distribution in summer months.

### Suggested cities + coordinates
| City | Latitude | Longitude |
|------|----------|-----------|
| Hong Kong | 22.32 | 114.17 |
| Stockholm | 59.33 | 18.07 |
| London | 51.51 | -0.13 |
| New York | 40.71 | -74.01 |

---

## Phase 2 — Polymarket (Prediction Market Data)

**URL:** https://polymarket.com/  
**Cost:** Free, public API  
**Docs:** https://docs.polymarket.com/

> Add Polymarket details here when entering Phase 2. Do not integrate before Phase 1 calibration is complete.

### What we use it for
- Market-implied probability P_market for matching weather events
- Input to edge calculation: edge = P_model - P_market

### Key endpoint (to fill in Phase 2)
```
GET https://clob.polymarket.com/markets
```

### ⚠️ Data availability constraint
Polymarket launched in 2020 and weather markets are relatively recent (2023–2024). **Do not assume historical data going back to 2015 exists.**

| Use case | Data available |
|----------|---------------|
| Phase 1 model calibration | 2015–2024 (Open-Meteo actuals) |
| Phase 2 edge backtest | ~6–12 months (limited by Polymarket history) |
| Phase 3 live | Current markets only |

This means the Phase 2 backtest will have a short history — that is expected and honest. State this explicitly in the notebook and README.

### Notes
- Polymarket uses USDC (on-chain)
- Markets are binary: YES/NO contracts priced [0, 1]
- Price of YES token ≈ market-implied probability (after adjusting for spread)
- Bid/ask spread is real — factor into effective_edge calculation (see math_reference.md)
- Platform fee ≈ 2% — also deducted from effective_edge
- Match events carefully: market description must align with your event definition exactly

---

## Config values (stored in `config/settings.py`)
```python
DEFAULT_CITY = "Hong Kong"
LATITUDE = 22.32
LONGITUDE = 114.17
TIMEZONE = "Asia/Hong_Kong"
HISTORICAL_START = "2015-01-01"     # for actuals (Open-Meteo archive)
HISTORICAL_END = "2024-12-31"       # for actuals
POLYMARKET_START = "2024-01-01"     # Polymarket data only reliable from ~2024
EVENT_THRESHOLD = 30.0              # °C
MIN_EDGE = 0.05                     # minimum gross edge to consider a signal
MIN_EFFECTIVE_EDGE = 0.02           # minimum edge after spread + fees
FRACTIONAL_KELLY = 0.25             # κ
FEE_RATE = 0.02                     # Polymarket platform fee (~2%)
```
