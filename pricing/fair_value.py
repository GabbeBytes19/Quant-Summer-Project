import re
import polars as pl
from config import settings
from data.fetcher import build_polymarket_price_dataset

def create_buckets(lower_bound,upper_bound):
    data = []
    for i in range(lower_bound,upper_bound):
        data.append((i,i+1))
    return data

def get_daily_bucket(df_result):
    buckets = []
    #df_result = build_polymarket_price_dataset() #Should we have this here , or take from jupyter df_result. Maybe more functons will need this call, need to make it smart, to get called once.
    df_bucuket_day = df_result["groupItemTitle"].to_list()
    for bucket in df_bucuket_day:
        #source: https://www.geeksforgeeks.org/python/python-extract-numbers-from-string/
        matches = re.findall(r'-?\d*\.?\d+', bucket) 
        res = [float(x) if '.' in x else int(x) for x in matches]
        res_int = int(res[0])
        if len(res) > 1:
            raise ValueError(f"Something is corrupted with the data,suppost to be one integer per line, now contains :  {res}")
        if "below" in bucket:
            lower_bound = None
            upper_bound = res_int

        elif "higher" in bucket:
            lower_bound = res_int
            upper_bound = None
        else:
            lower_bound = res_int
            upper_bound = res_int + 1
        
        buckets.append((lower_bound,upper_bound))
    return buckets

def get_bucket_polymarket(df_result,dailty_buckets,create_buckets):

    for low,high in buckets:
        if low is not None or high is not None: #closed bucket
            idx = buckets.index(low,high)

        if low is None: #open bucket
            while idx < len(buckets) and buckets[idx][1] is None:
                idx += 1
            idx = buckets.index(None,buckets[idx][1])

        if high is None: #open bucket
            while idx < len(buckets) and buckets[idx][0] is None:
                idx += 1
            idx = buckets.index(buckets[idx][0],None)
       

    df_result = df_result.join(pl.DataFrame({"bucket_index": idx}), on = "date", how = "left" )
    return df_result

def build_probability_vector(probability_function,buckets):
    lst = []
    for low,high in buckets:
        res = probability_function(low,high)
        lst.append(res)
    return lst


def build_daily_probability_vector(probability_function, buckets, days):
    lst = []
    for (low,high),day in zip(buckets,days): 
        res = probability_function(day,low,high)
        lst.append(res)
    return lst


def find_correct_bucket(actual_temp,buckets):
    for temp in buckets:
        if temp[0] <= actual_temp and temp[1] > actual_temp:
            return buckets.index(temp)
    raise ValueError(f"{actual_temp} not in any bucket")


