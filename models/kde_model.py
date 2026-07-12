import numpy as np
from scipy import stats

def kde_estimate(df,lower_bound,upper_bound):
    kde2 = stats.gaussian_kde(df,bw_method='silverman')
    P2 = kde2.integrate_box_1d(lower_bound,upper_bound)
    return P2
    