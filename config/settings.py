from datetime import datetime,timedelta
DEFAULT_CITY = "Hong Kong"  # Place
LATITUDE = 22.3020  # Latidue in the world
LONGITUDE = 114.1743  # Longtidue in the world
TIMEZONE = "Asia/Hong_Kong"  # Timezone
HISTORICAL_START = "2021-01-01"  # for actuals (Open-Meteo archive)
HISTORICAL_END = "2026-04-28"  # for actuals
FORECAST_START = "2017-01-01"  # for forecast (Open-Meteo historical forecast)
FORECAST_END = "2026-06-28"  # for forecast
EVENT_THRESHOLD = 30.0  # °C #Makes a binary event if the max daily temp at 2 meters is above this threshold
MIN_EDGE = 0.05  # minimum gross edge to consider a signal, Edge is models predicted probability - market probability, if edge is postive consider buying but only if it is above this threshold
MIN_EFFECTIVE_EDGE = 0.02  # minimum edge after spread + fees, the edge minus sprea(ask price -bidprice = bid/askprice on Polymarket) - fee_rate , act ifeffective egde is positive and above this threshold
FRACTIONAL_KELLY = 0.25  # κ take edge/net deciaml odds and multiply by this fraction to get the bet size, 0.25 is a conservative approach to reduce risk of ruin
ALPHA = 0.05  # α for VaR, the probability of loss exceeding the VaR threshold, 5% is a common choice for risk management
FEE_RATE = 0.02  # Polymarket platform fee (~2%), fee rate on polymarket
ASSUMED_SPREAD = 0.05  # Flat bid/ask spread assumption, Polymarket has no historical spread data for resolved markets, see docs/decisions_log.md
MAX_NULL_GAP = 5  # Maximum total number of null values allowed in the data, if there are more than this many nulls the dataset is discarded, otherwise they are interpolated
TOMMORROWS_DATE = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
LOWER_BOUND = 25  # Lower bound for the probability of the event, if the probability is below this threshold, consider it as a no-even
UPPER_BOUND= 36  # Upper bound for the probability of the event, if the probability is above this threshold, consider it as a yes-event
SPECIFIC_DAY = "2017-01-01"
IS_START = "2000-01-01" #In sample, data we have used to build the model
IS_END = "2016-12-31"
OOS_START = "2017-01-01" #Out sample, data the model never has seen
OOS_END = (datetime.now() -timedelta(days=1)).strftime('%Y-%m-%d')
MIN_FORECAST_HISTORY = 30  # Days of paired forecast/actual data required before a date is scored, so the forecast bias and sigma are estimated from earlier days only
USE_SYNTHECTIC_DATA = False #If you dont want to use real data with API calls, test data with Synthectic data,
POLYMARKET_START = "2026-01-01" ## Polymarket data only reliable from ~2024
POLYMARKET_END = "2026-04-28"
TODAYS_DATE_MINUS30 = (datetime.now() - timedelta(days = 30)).strftime('%Y-%m-%d')