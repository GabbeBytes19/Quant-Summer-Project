

from collections import defaultdict


def get_guessed_prob(prob_matrix,correct_indices_gauss):
    guessed_prob = []
    for probs,days in zip(prob_matrix,correct_indices_gauss):
        for idx,prob in enumerate(probs):
            if idx == days:
                guessed_prob.append((prob,1))
            else:
                guessed_prob.append((prob,0))

    return guessed_prob

def calculate_buckets(guessed_prob):
    prob_sums = defaultdict(float)
    binary_sums = defaultdict(float)
    counts = defaultdict(int)
    data = []
    for prob, binary in guessed_prob:
        bucket = min(int(prob * 10), 9)
        prob_sums[bucket] += prob
        binary_sums[bucket] += binary
        counts[bucket] += 1  

    for bucket in range(10):
        if counts[bucket]:
            mean_prob = prob_sums[bucket] / counts[bucket]
            mean_binary = binary_sums[bucket] / counts[bucket]
            prob_round = round(mean_prob, 3)
            prob_binary = round(mean_binary, 3)
            data.append((bucket,prob_round,prob_binary,counts[bucket]))
    return data
