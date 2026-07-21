from data import fetcher, cleaner,loader
from config import settings
from models.bayesian_model import bayesian_interference
from tests.fixtures.synthetic_data import synthetic_actual_df, synthetic_previous_df
import polars as pl
import pytest
import time


def test_sigma_posterior_raise(monkeypatch):
    #monkeypatch.setattr(fetcher, "fetch_data", lambda *args, **kwargs: synthetic_actual_df())
    #monkeypatch.setattr(fetcher,"fetch_previous_forecast_data",lambda *args, **kwargs: synthetic_previous_df())
    #monkeypatch.setattr(fetcher,"get_tommorows_wheather",lambda * args,**kwargs: 30)
    df_raw = fetcher.fetch_data(settings.HISTORICAL_START,settings.HISTORICAL_END)
    df_clean = cleaner.clean_data(df_raw)
    df_event = loader.add_event_column(df_clean)
    df_temp_summer = loader.filter_summer(df_event)
    df_pair = fetcher.call_fetcher_functions(settings.FORECAST_START,settings.FORECAST_END)
    df_temp_list = df_temp_summer["temperature_2m_max"].to_list()
    df_date_list = df_pair["date"].to_list()
    day = df_date_list[-1]
    sigma_posterior, sigma_prior,sigma_forecast, my_posterior,my_prior,likelihood_mean = bayesian_interference(df_temp_list,day,df_pair)

    assert sigma_posterior < sigma_prior
    assert sigma_posterior < sigma_forecast
    if my_prior > likelihood_mean:
        assert likelihood_mean < my_posterior < my_prior
    else:
         assert likelihood_mean > my_posterior > my_prior
