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
    print(cleaner.clean_data(df).null_count().to_numpy)
    res = cleaner.clean_data(df)
    assert res.null_count().pipe(sum).item() == 0
def test_date_is_valid():
    assert settings.HISTORICAL_END >= settings.HISTORICAL_START

def test_date_is_in_range_end():
    df = fetcher.fetch_data("2024-01-01", "2024-01-10")
    assert df["time"].max() <= settings.HISTORICAL_END
    assert df["time"].min() >= settings.HISTORICAL_START

