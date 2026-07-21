
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