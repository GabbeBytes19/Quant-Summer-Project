
from scipy.stats import norm
import numpy as np


def gaussian_probability(df_summer,lower_bound,upper_bound):
 
    lenght_df = len(df_summer)

    my = sum(df_summer)/lenght_df #Average of all values

    sigma = np.std(df_summer) #Standard deviation of all values
    if lower_bound is None and upper_bound is None:
        return None,my,sigma
    if lower_bound is not None and upper_bound is not None:
        P = norm.cdf((upper_bound-my)/sigma) -norm.cdf((lower_bound-my)/sigma) #Probability of the event happening between threshold_a and threshold_b
    if lower_bound is None and upper_bound is not None:
        P = norm.cdf((upper_bound-my)/sigma)
    if lower_bound is not None and upper_bound is None:
        P = 1 - norm.cdf((lower_bound-my)/sigma)
    return P,my,sigma
   

