from data import fetcher, cleaner,loader
from config import settings
from pricing import fair_value
from models import baseline
import polars as pl
import pytest
from models.bayesian_model import bayesian_interference
from tests.fixtures.synthetic_data import synthetic_actual_df, synthetic_previous_df

def test_create_buckets():
    buckets = fair_value.create_buckets(25,36)
    assert type(buckets) == list
    assert buckets[0] == (25,26)
    assert buckets[-1] == (35,36)
    assert len(buckets) == 11

def test_build_probability_vector(monkeypatch):
    monkeypatch.setattr(fetcher, "fetch_data", lambda *args, **kwargs: synthetic_actual_df())
    monkeypatch.setattr(fetcher,"fetch_previous_forecast_data",lambda *args, **kwargs: synthetic_previous_df())
    monkeypatch.setattr(fetcher,"get_tommorows_wheather",lambda * args,**kwargs: 30)
    df_raw = fetcher.fetch_data(settings.HISTORICAL_START,settings.HISTORICAL_END)
    df_clean = cleaner.clean_data(df_raw)
    df_event = loader.add_event_column(df_clean)
    df_temp_summer = loader.filter_summer(df_event)
    df_pair = fetcher.call_fetcher_functions(settings.FORECAST_START,settings.FORECAST_END)
    df_temp_list = df_pair["actual_temp"].to_list()
    df_temp_summer_list = df_temp_summer["temperature_2m_max"].to_list() 

    buckets = fair_value.create_buckets(25,36)
    probability_function = lambda low, high: baseline.gaussian_probability(df_temp_summer_list, low, high)[0]
    lst = fair_value.build_probability_vector(probability_function, buckets)
    assert abs(1 -sum(lst)) < 0.001
    assert len(lst) == len(buckets)
    for val in lst:
        assert 0<= val <= 1
    
    
def test_get_daily_bucket():
    fake_df = pl.DataFrame({
        "groupItemTitle": ["25°C", "20°C or below", "34°C or higher", "26°C", "20°C or below"]
    })

    buckets = fair_value.get_daily_bucket(fake_df)

    assert len(buckets) == fake_df.height
    assert buckets == [(25, 26), (None, 20), (34, None), (26, 27), (None, 20)]


def test_get_daily_bucket_raises_on_corrupted_title():
    fake_df = pl.DataFrame({"groupItemTitle": ["25-27°C"]})

    with pytest.raises(ValueError):
        fair_value.get_daily_bucket(fake_df)


def test_get_daily_bucket_feeds_build_probability_vector():
    fake_df = pl.DataFrame({
        "groupItemTitle": ["25°C", "20°C or below", "34°C or higher"]
    })

    buckets = fair_value.get_daily_bucket(fake_df)
    calls = []
    def probability_function(low, high):
        calls.append((low, high))
        return 0.5
    lst = fair_value.build_probability_vector(probability_function, buckets)

    assert len(lst) == len(buckets) == fake_df.height
    assert calls == [(25, 26), (None, 20), (34, None)]
    assert all(val == 0.5 for val in lst)


def test_find_correct_bucket(monkeypatch):
    monkeypatch.setattr(fetcher, "fetch_data", lambda *args, **kwargs: synthetic_actual_df())
    monkeypatch.setattr(fetcher,"fetch_previous_forecast_data",lambda *args, **kwargs: synthetic_previous_df())
    monkeypatch.setattr(fetcher,"get_tommorows_wheather",lambda * args,**kwargs: 30)
    buckets = fair_value.create_buckets(25,36)
    index1 = fair_value.find_correct_bucket(30.5,buckets)

    #assert index1 == 1
    with pytest.raises(ValueError):
        index2 = fair_value.find_correct_bucket(100,buckets)

    index3 = fair_value.find_correct_bucket(26,buckets)
    assert index3 == 1

  

# Source - https://stackoverflow.com/a/77304186
# Posted by Keith Smith
# Retrieved 7/23/2026, License - CC BY-SA 4.0
