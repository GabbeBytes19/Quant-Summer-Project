
def create_buckets(lower_bound,upper_bound):
    data = []
    for i in range(lower_bound,upper_bound):
        bucket_center = i + 0.5
        data.append((bucket_center))
    return data