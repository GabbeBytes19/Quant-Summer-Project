import polars as pl
import requests
import numpy as np
from config import settings

def store_data(start_date: str, end_date: str):
    items = {
        "latitude": settings.LATITUDE,
        "longitude": settings.LONGITUDE,
        "timezone": settings.TIMEZONE,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
    }
    url = "https://archive-api.open-meteo.com/v1/archive"

    return items, url

def fetch_data(start_date: str, end_date: str) -> pl.DataFrame:
    #What acaul happend, what the temperature actaully was
    items,url = store_data(start_date, end_date)
    
    try:
        data_json = requests.get(url, params=items, timeout=10)
        data = data_json.json()
        if "error" in data:
            raise ValueError(data["reason"])
        #print(data.keys())
        df_actual = pl.DataFrame(data["daily"])
        return df_actual
        
    except Exception as e:
        print(f"Error fetching data from {url} with params {items}: {e}")

def get_tommorows_wheather(tommorrows_date):
    items,_ =  store_data(tommorrows_date, tommorrows_date)
    url = "https://archive-api.open-meteo.com/v1/archive"
    try:
        data_json = requests.get(url, params=items, timeout=10)
        data = data_json.json()
        if "error" in data:
            raise ValueError(data["reason"])
        #print(data.keys())
        df = pl.DataFrame(data["daily"])
        df_tommorrow = df["temperature_2m_max"].to_list()
        return df_tommorrow[0]
    except Exception as e:
        print(f"Error fetching data from {url} with params {items}: {e}")


def fetch_historical_forecest_data(start_date: str, end_date: str):
    #What the forecast model predicted whould happend.
    items,_ = store_data(start_date, end_date)
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    try:
        data_json = requests.get(url, params=items, timeout=10)
        data = data_json.json()
        if "error" in data:
            raise ValueError(data["reason"])
        #print(data.keys())
        df_predicted = pl.DataFrame(data["daily"])
        return df_predicted
        
    except Exception as e:
        print(f"Error fetching data from {url} with params {items}: {e}")


def pair_dataframes():
    df_actual = fetch_data(settings.HISTORICAL_START, settings.HISTORICAL_END)
    df_predicted = fetch_historical_forecest_data(settings.HISTORICAL_START, settings.HISTORICAL_END)
    df_dates = df_actual.get_column("time")
    df_actual_temp = df_actual.get_column("temperature_2m_max").alias("actual_temp")
    df_predicted_temp = df_predicted.get_column("temperature_2m_max").alias("predicted_temp")
    df_pair = pl.DataFrame([df_dates, df_actual_temp, df_predicted_temp])
    return df_pair

def compute_forecast_error(df_pair):
    #Some of the errors probably gonna work , or both
    #df_error = df_pair.with_columns( (pl.nth(1)) - (pl.nth(2)))
    #df_error2 = df_pair.with_columns( pl.col("predicted_temp") - pl.col("actual_temp"))
    error = df_pair.with_columns((pl.col("predicted_temp") - pl.col("actual_temp"))).to_series().to_list().std()

    return error