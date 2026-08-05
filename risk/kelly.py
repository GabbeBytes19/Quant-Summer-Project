
import polars as pl
from config import settings

def kelly_criterion(p_model,market_odds):

    b = (1 - market_odds) / market_odds
    p =  pl.Series(p_model)
    q = 1 -p
    f_star = (b*p-q ) / b
    #f_star = edge / b ?
    return f_star * settings.FRACTIONAL_KELLY
