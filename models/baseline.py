
from scipy.stats import norm
import numpy as np


def gaussian_probability(df_summer,threshold):
 
    lenght_df = len(df_summer)

    my = sum(df_summer)/lenght_df #Average of all values

    sigma = np.std(df_summer) #Standard deviation of all values

    P = 1 -  norm.cdf((threshold-my)/sigma)  
    
    return P,my,sigma
