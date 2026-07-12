from scipy.stats import norm
from data import fetcher
from config import settings
import numpy as np


def bayesian_interference(df_summer):
    #Prior
    true_my = np.mean(df_summer)
    true_sigma = np.std(df_summer)
    #Likelihood
    forecast_value = fetcher.get_tommorows_wheather(settings.TOMMORROWS_DATE,settings.TOMMORROWS_DATE)

