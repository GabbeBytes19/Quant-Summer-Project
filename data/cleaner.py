from config import settings
import polars as pl

def clean_data(df):
    # If the data is not correct format or are missing values , we need to clean the data and return a clean dataframe
    # If its less than 5 nulls in a row --> interpolate , else --> discard the data
    orignal_length = len(df)
    if df[
        "time", "temperature_2m_max", "temperature_2m_min", "precipitation_sum"
    ].is_empty():
        return None

    if (
        df["time", "temperature_2m_max", "temperature_2m_min", "precipitation_sum"]
        .null_count().pipe(sum).item() > 0
    ):
        df = df.interpolate()
        df = df.drop_nulls()

    if orignal_length - len(df) > settings.MAX_NULL_GAP:
        return None

    return df



# Source - https://stackoverflow.com/a/78350448
# Posted by Hericks, modified by community. See post 'Timeline' for change history
# Retrieved 6/30/2026, License - CC BY-SA 4.0

