import numpy as np
from scipy import stats

def kde_estimate(df,lower_bound,upper_bound):
    kde = stats.gaussian_kde(df,bw_method='silverman')
    P = kde.integrate_box_1d(lower_bound,upper_bound)
    return P
    