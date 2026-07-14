import polars as pl
import requests
import numpy as np
import math
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
    url = "https://historical-forecast-api.open-meteo.com/v1/forecast"
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
    url = "https://historical-forecast-api.open-meteo.com/v1/forecast"
    
    try:
        data_json = requests.get(url, params=items, timeout=10)
        data = data_json.json()
        print(data["daily"].keys())
        print(data)
        if "error" in data:
            raise ValueError(data["reason"])
        #print(data.keys())
        df_predicted = pl.DataFrame(data["daily"])
        return df_predicted
        
    except Exception as e:
        print(f"Error fetching data from {url} with params {items}: {e}")


def fetch_previous_forecast_data():
    items = {
        "latitude": settings.LATITUDE,
        "longitude": settings.LONGITUDE,
        "hourly": "temperature_2m_previous_day1,temperature_2m_previous_day2,temperature_2m_previous_day3,temperature_2m_previous_day4,temperature_2m_previous_day5",
        "past_days": "1900",
        "forecast_days": "1",
    }
    url = "https://previous-runs-api.open-meteo.com/v1/forecast"
    try:
        data_json = requests.get(url, params=items, timeout=120)
        data = data_json.json()
        if "error" in data:
            raise ValueError(data["reason"])
        df_previous = pl.DataFrame(data["hourly"])
        return df_previous

    except Exception as e:
        print(f"Error fetching data from {url} with params {items}: {e},Kolla vi kom hit hahaha")



def pair_dataframes():
    df_actual = fetch_data(settings.FORECAST_START, settings.FORECAST_END)
    df_predicted = fetch_historical_forecest_data(settings.FORECAST_START, settings.FORECAST_END)
    df_dates = df_actual.select(pl.col("time").alias("date"))
    df_actual_temp = df_actual.select(pl.col("temperature_2m_max").alias("actual_temp"))
    df_predicted_temp = df_predicted.select(pl.col("temperature_2m_max").alias("predicted_temp"))
    #df_pair = pl.DataFrame([df_dates, df_actual_temp, df_predicted_temp])
    df_pair = pl.concat([df_dates, df_actual_temp, df_predicted_temp], how="horizontal")
    return df_pair

def compute_forecast_error(df_pair):
    #Some of the errors probably gonna work , or both
    #df_error = df_pair.with_columns( (pl.nth(1)) - (pl.nth(2)))
    #df_error2 = df_pair.with_columns( pl.col("predicted_temp") - pl.col("actual_temp"))
    error_list = df_pair.select((pl.col("predicted_temp") - pl.col("actual_temp"))).to_series().to_list()
    mean_error = np.mean(error_list)
    delta_error = 0
    for error in error_list:
        delta_error += (error - mean_error) **2
    res= delta_error / len(error_list)
    return error_list,math.sqrt(res)
    
      

    