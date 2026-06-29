import polars as pl
import requests

from config import settings


def fetch_data(start_date: str, end_date: str) -> pl.DataFrame:
    items = {
        "latitude": settings.LATITUDE,
        "longitude": settings.LONGITUDE,
        "timezone": settings.TIMEZONE,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
    }
    url = "https://archive-api.open-meteo.com/v1/archive"
    try:
        data_json = requests.get(url, params=items, timeout=10)
        data = data_json.json()
        df = pl.DataFrame(data)
        return df
    except Exception as e:
        print(f"Error fetching data from {url} with params {items}: {e}")
