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


def fetch_previous_forecast_data(start_date: str, end_date: str) -> pl.DataFrame:
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



def get_daily_max(df_previous): #Maybe moved to data/loader
    # Get the daily max temperature for each of the previous days
    df_daily_max = df_previous.group_by(pl.col("time").str.slice(0, 10).alias("date")).agg(
    pl.col("temperature_2m_previous_day1").max().alias("daily_max_predicted")).sort("date")
    return df_daily_max

def pair_dataframes(df_actual,df_daily_max_predicted):
    df_actual = df_actual.select(
        pl.col("time").alias("date"),
        pl.col("temperature_2m_max").alias("actual_temp"),
    )
    
    df_pair = df_actual.join(df_daily_max_predicted, on="date", how="inner").drop_nulls().sort("date")
    return df_pair

def get_specific_day(day : str,df_pair):
  
    df_get_day_temp = df_pair.filter(pl.col("date") == day)
    if df_get_day_temp.is_empty():
        return f"{day} is not a date in the DataFrame"
    df_get_day_temp_list = df_get_day_temp["daily_max_predicted"].to_list()
    return df_get_day_temp_list[0]


def call_fetcher_functions(start_date, end_date):
   df = fetch_data(start_date,end_date)
   df_previous = fetch_previous_forecast_data(start_date,end_date)    
   df_daily_max = get_daily_max(df_previous)
   df_pair = pair_dataframes(df,df_daily_max)
   return df_pair
  


def compute_forecast_error(df_pair): #This maybe should be moved to models/
    error_list = df_pair.select((pl.col("daily_max_predicted") - pl.col("actual_temp"))).to_series().to_list()
    mean_error = np.mean(error_list)
    delta_error = 0
    for error in error_list:
        delta_error += (error - mean_error) **2
    res= delta_error / len(error_list)
    return error_list,mean_error,math.sqrt(res)
    
      

    