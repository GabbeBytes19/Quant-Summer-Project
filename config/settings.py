from datetime import datetime,timedelta
DEFAULT_CITY = "Hong Kong"  # Place
LATITUDE = 22.3020  # Latidue in the world
LONGITUDE = 114.1743  # Longtidue in the world
TIMEZONE = "Asia/Hong_Kong"  # Timezone
HISTORICAL_START = "2021-01-01"  # for actuals (Open-Meteo archive)
HISTORICAL_END = "2026-04-28"  # for actuals
FORECAST_START = "2017-01-01"  # for forecast (Open-Meteo historical forecast)
FORECAST_END = "2026-06-28"  # for forecast
POLYMARKET_START = "2024-01-01"  # Polymarket data only reliable from ~2024
EVENT_THRESHOLD = 30.0  # °C #Makes a binary event if the max daily temp at 2 meters is above this threshold
MIN_EDGE = 0.05  # minimum gross edge to consider a signal, Edge is models predicted probability - market probability, if edge is postive consider buying but only if it is above this threshold
MIN_EFFECTIVE_EDGE = 0.02  # minimum edge after spread + fees, the edge minus sprea(ask price -bidprice = bid/askprice on Polymarket) - fee_rate , act ifeffective egde is positive and above this threshold
FRACTIONAL_KELLY = 0.25  # κ take edge/net deciaml odds and multiply by this fraction to get the bet size, 0.25 is a conservative approach to reduce risk of ruin
FEE_RATE = 0.02  # Polymarket platform fee (~2%), fee rate on polymarket
MAX_NULL_GAP = 5  # Maximum number of consecutive null values allowed in the data before discarding the data, if there are more than this number of consecutive nulls, discard the data
TOMMORROWS_DATE = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
LOWER_BOUND = 31.5  # Lower bound for the probability of the event, if the probability is below this threshold, consider it as a no-even
UPPER_BOUND= 32.5  # Upper bound for the probability of the event, if the probability is above this threshold, consider it as a yes-event
SPECIFIC_DAY = "2017-01-01"