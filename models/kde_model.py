import numpy as np
import math
from scipy import stats

def kde_estimate(df,lower_bound,upper_bound):
    kde = stats.gaussian_kde(df,bw_method='silverman')
    if lower_bound is None and upper_bound is None:
        return 1
    if lower_bound is None:
        lower_bound = -np.inf
    if upper_bound is None:
        upper_bound = np.inf
    P = kde.integrate_box_1d(lower_bound,upper_bound)
    return P
    