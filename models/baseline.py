
from scipy.stats import norm
import numpy as np


def gaussian_probability(df_summer,bucket_center):
 
    lenght_df = len(df_summer)

    my = sum(df_summer)/lenght_df #Average of all values

    sigma = np.std(df_summer) #Standard deviation of all values

    P = norm.cdf((bucket_center+0.5-my)/sigma) -norm.cdf((bucket_center-0.5-my)/sigma) #Probability of the event happening between threshold_a and threshold_b
    
    return P,my,sigma


