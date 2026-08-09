import polars as pl
import requests
import numpy as np
import math
import time
from config import settings
from data.loader import filter_resolved,add_market_prob_column,join_price_lookup
from data.cleaner import clean_polymarket_data
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
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
        raise ValueError(f"Error fetching data from {url} with params {items}: {e}")


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
        raise ValueError(f"Error fetching data from {url} with params {items}: {e}")


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
        raise ValueError(f"Error fetching data from {url} with params {items}: {e}")

"""
def parse_date_function_helper():
    list_of_dates = []
    month_converter = {1:'january',
		2:'february',
		3:'march',
		4:'april',
		5:'may',
		6:'june',
		7:'july',
		8:'august',
		9:'september',
		10:'october',
		11:'november',
		12:'december'		}
    from datetime import datetime,timedelta
    start_date_str = settings.POLYMARKET_START 
    end_date_str = settings.POLYMARKET_END 
    # Source - https://stackoverflow.com/a/1060330
    # Posted by Ber, modified by community. See post 'Timeline' for change history
    # Retrieved 7/27/2026, License - CC BY-SA 4.0
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    day_count = int((end_date - start_date).days)
    for single_date in (start_date + timedelta(n) for n in range(day_count +1 )):
        #print(single_date) # Gives us all the dates!
        year = single_date.year
        month_str = single_date.month
        month = month_converter[single_date.month]
        day = single_date.day
        list_of_dates.append((month,month_str,day,year))
    return list_of_dates
   

def fetch_polymarket_data():
    lst = parse_date_function_helper()
    all_days = []
    url = "https://gamma-api.polymarket.com/events"
    for month,month_str, day, year in lst:
        items = {"slug": f"highest-temperature-in-hong-kong-on-{month}-{day}-{year}"}
        try:
            response = requests.get(url, params=items, timeout=120)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            raise ValueError(f"Error fetching data from {url} with params {items}: {e}")

        if not data or "markets" not in data[0]:
            continue
        
        df_day = pl.DataFrame(data, strict=False).explode("markets").with_columns(pl.lit(f"{year}-{month_str:02d}-{day:02d}").alias("date"))
        all_days.append(df_day)

    return pl.concat(all_days,how="diagonal_relaxed")

"""

def fetch_polymarket_data():
    url = "https://gamma-api.polymarket.com/events"
    all_pages = []
    offset = 0
    while True:
        items = {"series_id": 11312, "limit": 100, "offset": offset}
        try:
            response = requests.get(url, params=items, timeout=120)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            raise ValueError(f"Error fetching data from {url} with params {items}: {e}")

        if not data:
            break

        all_pages.append(pl.DataFrame(data, strict=False).explode("markets"))
        offset += 100
    return pl.concat(all_pages, how="diagonal_relaxed")



def fetch_all_price_history(token_ids,date):
    all_histories = []
    start = time.perf_counter()
    progress = len(token_ids)
    with ThreadPoolExecutor(max_workers=15) as executor:
        results = executor.map(fetch_polymarket_price_history, token_ids,date)
        for token_idx, (token_id, history_df) in enumerate(zip(token_ids, results)):
            all_histories.append(history_df.with_columns(pl.lit(token_id).alias("yes_token_id")))
            if (token_idx + 1) % 50 == 0:
                print(f"We are on {token_idx + 1} of {progress}, this took{ time.perf_counter() - start} seconds ")
        
    return pl.concat(all_histories, how="diagonal_relaxed").sort("yes_token_id","t")
 
def fetch_polymarket_price_history(clob_token_id,date):
    items =  {
    "market": clob_token_id,
    "interval": "max"
    }
    url = "https://clob.polymarket.com/prices-history"
    try:
        if date >= settings.TODAYS_DATE_MINUS30:
            data_json = requests.get(url, params=items, timeout=120)
            data = data_json.json()
            if "error" in data:
                raise ValueError(data["reason"])
            df_polymarket_history= pl.DataFrame(data["history"])
            
        else:
            items["fidelity"] = 1440
            try:
                data_json = requests.get(url, params=items, timeout=120)
                data = data_json.json()
                if "error" in data:
                        raise ValueError(data["reason"])
                df_polymarket_history= pl.DataFrame(data["history"])
                return df_polymarket_history
            except Exception as e:
                raise ValueError(f"Error fetching data from {url} with params {items}: {e}")
        
        return df_polymarket_history

    except Exception as e:
        raise ValueError(f"Error fetching data from {url} with params {items}: {e}")


def get_spread_polymarket():
    #Source : https://docs.polymarket.com/api-reference/market-data/get-spread


    #df_list = df_result["yes_token_id"].to_list()
    #token_id = df_list[0]
    token_id = '100219190591120160966457091003186951399728474447451634780784282957470581045794' 
    dt_start = datetime.strptime("2026-05-30", "%Y-%m-%d")
    dt_end = datetime.strptime("2026-05-31", "%Y-%m-%d")
    milliseconds_start = int(dt_start.timestamp() * 1000)
    milliseconds_end = int(dt_end.timestamp() * 1000)
    items = {
            "token_id" : token_id,
            "start_time": milliseconds_start,
            "end_time": milliseconds_end,
    }
    #url = "https://clob.polymarket.com/spread"
    url = "https://api.domeapi.io/v1/polymarket/orderbooks"
    try:
        data_json = requests.get(url, params=items, timeout=120)
        print(data_json)
        data = data_json.json()
        print(data)
        if "error" in data:
            raise ValueError(data["error"])
        #df_polymarket_history= pl.DataFrame(data["history"])
    except ValueError:
        print(f"Error fetching data from {url} with params {items}")
    return data

        

def build_polymarket_price_dataset():
    start = time.perf_counter()
    df = fetch_polymarket_data()
    print("fetch_polymarket_data klar efter:", time.perf_counter() - start, "sekunder")
    df_clean = clean_polymarket_data(df)
    print("clean_polymarket_data klar efter:", time.perf_counter() - start, "sekunder")
    df_filtered = filter_resolved(df_clean)
    print("filter_resolved klar efter:", time.perf_counter() - start, "sekunder")
    df_loaded = add_market_prob_column(df_filtered)

    df_prices = fetch_all_price_history(df_loaded["yes_token_id"],df_loaded["date"]) #thread
    print("fetch_all_price_history:", time.perf_counter() - start, "sekunder")
    df_prices = df_prices.drop_nulls()
    df_result = join_price_lookup(df_loaded,df_prices)
    return df_result



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
        raise ValueError( f"{day} is not a date in the DataFrame")
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
    
      

    


#except Exception as e:
#raise ValueError(f"Error fetching data from {url} with params {items}: {e}")
# Source - https://stackoverflow.com/a/75628511
# Posted by jqurious, modified by community. See post 'Timeline' for change history
# Retrieved 7/27/2026, License - CC BY-SA 4.0