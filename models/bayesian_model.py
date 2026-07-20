from scipy.stats import norm
from data import fetcher
from config import settings
from models.baseline import gaussian_probability
import numpy as np


def bayesian_interference(df_summer):
    #Prior
    true_my = np.mean(df_summer)
    #Likelihood
    forecast_value = fetcher.get_tommorows_wheather(settings.TOMMORROWS_DATE)
    _,mean_error,sigma_forecast= fetcher.compute_forecast_error()
    _,my_prior,sigma_prior = gaussian_probability(df_summer,settings.lower_bound,settings.upper_bound)

    likelihood_mean = forecast_value - mean_error
    sigma_forecast_squared= sigma_forecast**2
    true_sigma_precision = 1/sigma_forecast_squared

    prior_sigma_squared = sigma_prior**2 
    prior_sigma_precision = 1/prior_sigma_squared

    combined_precision = true_sigma_precision + prior_sigma_precision
    posterior_variance = 1/combined_precision

    sigma_posterior = np.sqrt(posterior_variance)


    if sigma_posterior > sigma_prior or sigma_posterior > sigma_forecast:
        raise ValueError("Posterior standard deviation is less than prior or true standard deviation, which is not expected.")


    true_my_squared = true_my * prior_sigma_precision
    likelihood_mean_squared = likelihood_mean * true_sigma_precision

    my_posterior = (likelihood_mean_squared + true_my_squared) / combined_precision

    if my_posterior > my_prior and my_posterior > likelihood_mean or my_posterior < my_prior and my_posterior < likelihood_mean:
        raise ValueError("Posterir mean should be less than prior or true standar my")


    return sigma_posterior, sigma_prior,sigma_forecast, my_posterior,my_prior,likelihood_mean


def posterior_probability(df_summer,lower_bound,upper_bound):
    sigma_posterior,_,_,my_posterior,_,_ = bayesian_interference(df_summer)
     
    if lower_bound is None and upper_bound is None:
        return None
     
    if lower_bound is not None and upper_bound is not None:
        P = norm.cdf((upper_bound-my_posterior)/sigma_posterior) -norm.cdf((lower_bound-my_posterior)/sigma_posterior) #Probability of the event happening between threshold_a and threshold_b
    if lower_bound is None and upper_bound is not None:
        P = norm.cdf((upper_bound-my_posterior)/sigma_posterior)
    if lower_bound is not None and upper_bound is None:
        P = 1 - norm.cdf((lower_bound-my_posterior)/sigma_posterior)

    return P