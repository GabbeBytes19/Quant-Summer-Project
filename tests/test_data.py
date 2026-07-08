from data import fetcher, cleaner
from config import settings
import polars as pl
import pytest


def test_columns_correct():
    df = fetcher.fetch_data("2024-01-01", "2024-01-10")
    assert set(df.columns) == {
        "time", 
        "temperature_2m_max", 
        "temperature_2m_min", 
        "precipitation_sum"
    }

def test_checks_nulls():
    df = fetcher.fetch_data("2024-01-01", "2024-01-10")
    assert cleaner.clean_data(df) is not None

def test_date_is_valid():
    assert settings.start_date[0:4] >= settings.HISTORICAL_START[0:4]
    if settings.start_date[0:4] == settings.HISTORICAL_START[0:4]:
        assert settings.start_date[5:7] >= settings.HISTORICAL_START[5:7]
        if settings.start_date[5:7] == settings.HISTORICAL_START[5:7]:
            assert settings.start_date[8:10] >= settings.HISTORICAL_START[8:10] 

def test_date_is_in_range_end():
    df = fetcher.fetch_data("2024-01-01", "2024-01-10")
    assert df["time"].max() <= settings.HISTORICAL_END
    assert df["time"].min() >= settings.HISTORICAL_START