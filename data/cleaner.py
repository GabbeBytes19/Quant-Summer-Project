from config import settings


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
        .is_null()
        .any()
    ):
        df = df.interpolate()
        df = df.drop_nulls()

    if orignal_length - len(df) > settings.MAX_NULL_GAP:
        return None

    return df
