# Data Sources

---

## Phase 1, Open-Meteo (Weather Data)

**URL:** https://open-meteo.com/  
**Cost:** Free, no API key required  
**Docs:** https://open-meteo.com/en/docs

### Look Ahead Bias Warning
The archive endpoint returns **observed actuals**, what really happened. This is correct for scoring model predictions, but **must never be used as input features for training**. A model trained on actuals would implicitly "know the future."

For Phase 1, the safe approach is **walk forward validation**. Train only on data strictly before date t, predict for t, and score against actuals at t. Never let actuals at t leak into the training window.

For more realistic simulation (Phase 2+), use the **historical forecast endpoint** which returns what NWP models predicted at time t, i.e. the information actually available at decision time.

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

### Historical forecast endpoint (for training features, avoids look ahead bias)
```
GET https://historical-forecast-api.open-meteo.com/v1/forecast
```
Returns what forecast models predicted at each past date, the information that was actually available. Use this as model input features to avoid look ahead bias.

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
Recommended starting threshold is **30°C** (typical Hong Kong summer day).
This gives a roughly balanced class distribution in summer months.

### Suggested cities + coordinates
| City | Latitude | Longitude |
|------|----------|-----------|
| Hong Kong | 22.32 | 114.17 |
| Stockholm | 59.33 | 18.07 |
| London | 51.51 | -0.13 |
| New York | 40.71 | -74.01 |

---

## Phase 2, Polymarket (Prediction Market Data)

**URL:** https://polymarket.com/  
**Cost:** Free, public API  
**Docs:** https://docs.polymarket.com/

### What we use it for
- Market implied probability P_market for matching weather events
- Used as input to the edge calculation, edge = P_model - P_market

### Endpoints actually used (as of Phase 2/3 completion, 2026-08-11)
```
GET https://gamma-api.polymarket.com/events         # market discovery, paginated by series_id, unbounded/live (data/fetcher.py:fetch_polymarket_data)
GET https://clob.polymarket.com/prices-history       # per token historical price series, used for market_prob/edge (data/fetcher.py:fetch_polymarket_price_history)
```
`GET https://clob.polymarket.com/markets` (listed here previously) was never actually used, market discovery goes through the Gamma API's `/events` endpoint instead.

### Live/bulk request rate limiting, confirmed 2026-08
Both the Gamma API and the CLOB price history endpoint have shown `ConnectionResetError`/SSL handshake failures during this project's bulk fetches (`fetch_all_price_history` hits ~1600+ tokens via 15 concurrent workers). Confirmed via testing that this happens both under heavy concurrency *and* in a plain sequential loop after enough total requests, pointing to request volume based throttling (client side or server side) rather than a burst/concurrency specific issue. No fix implemented beyond retrying. Reducing concurrency and/or adding inter request delay are the untried mitigations if this becomes a persistent blocker.

### No historical bid/ask spread data exists for resolved markets
Live `/spread` and `/book` CLOB endpoints only return data for currently open markets, every market in this project is `closed == True` (already resolved), so these consistently return `{'error': 'No orderbook exists for the requested token id'}`. No historical order book endpoint exists on Polymarket's own API. Third party sources were checked and ruled out. **Dome API** (real, but Polymarket acquired Dome and shut down all Dome APIs by 2026-04-28), **PolymarketData.co** (real, but paid/tiered), **Bitquery** (provides trade data, not order book data, also paid), and **pmxt** (real library, but appears live only, no historical date parameter). `pricing/edge.py:effective_edge()` uses a flat, documented placeholder spread constant instead, a permanent decision, see `decisions_log.md`.

### Data availability constraint
Polymarket launched in 2020 and weather markets are relatively recent (2023–2024). **Do not assume historical data going back to 2015 exists.**

| Use case | Data available |
|----------|---------------|
| Phase 1 model calibration | 2015–2024 (Open-Meteo actuals) |
| Phase 2 edge backtest | ~6–12 months (limited by Polymarket history) |
| Phase 3 live | Current markets only |

This means the Phase 2 backtest will have a short history, that is expected and honest. State this explicitly in the notebook and README.

### Notes
- Polymarket uses USDC (on chain)
- Markets are binary: YES/NO contracts priced [0, 1]
- Price of YES token ≈ market implied probability (after adjusting for spread)
- Bid/ask spread is real, factor into effective_edge calculation (see math_reference.md)
- Platform fee ≈ 2%, also deducted from effective_edge
- Match events carefully: market description must align with your event definition exactly

### Bucket boundaries are per day, not fixed, confirmed 2026-07-30

Each Hong Kong daily temperature event is split into several bucket markets (`groupItemTitle`/`groupItemThreshold` per row), but **the actual temperature range covered shifts day to day around that day's forecast**, it is not a fixed global grid. This was confirmed directly by comparing real data. 2026-07-19 and 2026-07-20 both used an 11 bucket set spanning 25°C–35°C, while 2026-05-20 used an 11 bucket set spanning roughly 20°C–30°C instead. Same bucket *count*, different bucket *range*.

**Practical consequence.** The model's own fixed grid (`pricing.fair_value.create_buckets(25, 36)`, used throughout Phase 1) must **not** be reused to compute "model fair value" against a specific Polymarket row, that day's actual bucket edges have to be parsed from its own `groupItemTitle` instead.

**`groupItemTitle` string shapes and how they map to `(lower_bound, upper_bound)`** (matching the convention of using `None` for an open ended side, already used by `gaussian_probability`/`kde_estimate`/`posterior_probability`).
| `groupItemTitle` shape | Example | `(lower_bound, upper_bound)` |
|---|---|---|
| `"X°C"` (plain bucket) | `"21°C"` | `(21, 22)`, same 1 degree width as `create_buckets`' `(i, i+1)` |
| `"X°C or below"` (open below tail) | `"20°C or below"` | `(None, 20)` |
| `"X°C or higher"` (open above tail) | `"34°C or higher"` | `(34, None)` |

Each row is parsed independently, the two tail buckets are separate rows/outcomes on the same day, not endpoints of one combined interval.

---

## Config values (full contents of `config/settings.py`, current as of 2026-08-11)
```python
DEFAULT_CITY = "Hong Kong"
LATITUDE = 22.3020
LONGITUDE = 114.1743
TIMEZONE = "Asia/Hong_Kong"
HISTORICAL_START = "2021-01-01"     # for actuals (Open-Meteo archive)
HISTORICAL_END = "2026-04-28"       # for actuals
FORECAST_START = "2017-01-01"       # for forecast (Open-Meteo historical forecast)
FORECAST_END = "2026-06-28"
EVENT_THRESHOLD = 30.0              # °C
MIN_EDGE = 0.05                     # minimum gross edge to consider a signal
MIN_EFFECTIVE_EDGE = 0.02           # minimum edge after spread + fees
FRACTIONAL_KELLY = 0.25             # κ
ALPHA = 0.05                        # α for VaR (5th percentile)
FEE_RATE = 0.02                     # Polymarket platform fee (~2%)
MAX_NULL_GAP = 5                    # max consecutive nulls tolerated before discarding a data run
LOWER_BOUND = 25                    # lower edge of the fixed climatology bucket grid
UPPER_BOUND = 36                    # upper edge of the fixed climatology bucket grid
SPECIFIC_DAY = "2017-01-01"
IS_START = "2000-01-01"             # in-sample: used to build the model
IS_END = "2016-12-31"
OOS_START = "2017-01-01"            # out-of-sample: never seen by the model
USE_SYNTHECTIC_DATA = True          # only swaps fetch_data (weather actuals) for synthetic — does NOT cover Polymarket fetching
POLYMARKET_START = "2026-01-01"     # bounds only apply if the (currently dead-code) slug-based fetch path is used — see fetcher.py
POLYMARKET_END = "2026-04-28"
```
**Dynamic, not fixed.** `OOS_END`, `TOMMORROWS_DATE`, and `TODAYS_DATE_MINUS30` are all computed from `datetime.now()` at import time (e.g. `OOS_END` = yesterday), they shift every day, which is part of why exact backtest results aren't perfectly reproducible run to run (see `decisions_log.md`, Phase 2/3 Summary).

**Note.** `fetch_polymarket_data()` in `data/fetcher.py` currently fetches the *entire* history of `series_id: 11312` (unbounded, paginated), ignoring `POLYMARKET_START`/`POLYMARKET_END`, an earlier date range based version of this function exists in the file but is dead code (sits inside a docstring/comment block), never executed.
