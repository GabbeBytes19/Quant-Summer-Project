
def create_buckets(lower_bound,upper_bound):
    data = []
    for i in range(lower_bound,upper_bound):
        data.append((i,i+1))
    return data

def build_probability_vector(probability_function,buckets):
    lst = []
    for low,high in buckets:
        res = probability_function(low,high)
        lst.append(res)
    return lst


def find_correct_bucket(actual_temp,buckets):
    for temp in buckets:
        if temp[0] <= actual_temp and temp[1] > actual_temp:
            return buckets.index(temp)
    raise ValueError(f"{actual_temp} not in any bucket")

