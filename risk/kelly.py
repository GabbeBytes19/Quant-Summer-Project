
import polars as pl
from config import settings

def kelly_criterion(p_model,market_odds):
    market_odds_series = pl.Series(market_odds)
    b = (1 - market_odds_series) / market_odds_series
    p =  pl.Series(p_model)
    q = 1 -p
    f_star = (b*p-q ) / b
    #f_star = edge / b ?
    return f_star * settings.FRACTIONAL_KELLY
