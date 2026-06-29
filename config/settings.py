DEFAULT_CITY = "Linköping"  # Place
LATITUDE = 58.41  # Latidue in the world
LONGITUDE = 15.62  # Longtidue in the world
TIMEZONE = "Europe/Stockholm"  # Timezone
HISTORICAL_START = "2000-01-01"  # for actuals (Open-Meteo archive)
HISTORICAL_END = "2024-12-31"  # for actuals
POLYMARKET_START = "2024-01-01"  # Polymarket data only reliable from ~2024
EVENT_THRESHOLD = 25.0  # °C #Makes a binary event if the max daily temp at 2 meters is above this threshold
MIN_EDGE = 0.05  # minimum gross edge to consider a signal, Edge is models predicted probability - market probability, if edge is postive consider buying but only if it is above this threshold
MIN_EFFECTIVE_EDGE = 0.02  # minimum edge after spread + fees, the edge minus sprea(ask price -bidprice = bid/askprice on Polymarket) - fee_rate , act ifeffective egde is positive and above this threshold
FRACTIONAL_KELLY = 0.25  # κ take edge/net deciaml odds and multiply by this fraction to get the bet size, 0.25 is a conservative approach to reduce risk of ruin
FEE_RATE = 0.02  # Polymarket platform fee (~2%), fee rate on polymarket
