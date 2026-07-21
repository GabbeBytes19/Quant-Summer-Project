import numpy as np

def create_buckets(lower_bound,upper_bound):
    data = []
    for i in range(lower_bound,upper_bound):
        bucket_center = i + 0.5
        data.append((bucket_center))




def brier_score(prob_matrix, correct_indices):
    running_total = 0
    for day_probs,correct_class in zip(prob_matrix,correct_indices):
        res = 0
        right_prob = day_probs[correct_class]
        for day in day_probs:
            res += day ** 2  
        days_points = 1 - (2*right_prob) + res
        running_total += days_points

    return running_total / len(prob_matrix)


def log_loss(prob_matrix, correct_indices,epsilon):
    running_total = 0
    for day_probs,correct_class in zip(prob_matrix,correct_indices):
        right_prob = max(day_probs[correct_class],epsilon) #TO discard the value to not get log(0)
        log_loss = -np.log(right_prob)
        running_total += log_loss
    return running_total / len(prob_matrix)
    