from config import settings
from data import fetcher, cleaner,loader
from config import settings
from models.bayesian_model import bayesian_interference
from tests.fixtures.synthetic_data import synthetic_actual_df, synthetic_previous_df
from pricing.fair_value import create_buckets
from models.baseline import gaussian_probability
from models.kde_model import kde_estimate
from models.bayesian_model import posterior_probability
from evaluation.eval_loop import run_eval
from evaluation.scoring import brier_score , log_loss, skill_score
from evaluation.calibration import  get_guessed_prob,calculate_buckets

def use_synthectic_data():
    if settings.USE_SYNTHECTIC_DATA:
        fetch_data = lambda *args, **kwargs: synthetic_actual_df()
        fetch_previous_forecast_data = lambda *args, **kwargs: synthetic_previous_df()
        get_tommorows_wheather = lambda *args, **kwargs: 30
    else:
        pass
def fetch_data():
    use_synthectic_data()

    df_raw = fetcher.fetch_data(settings.IS_START,settings.IS_END)
    df_clean = cleaner.clean_data(df_raw)
    df_event = loader.add_event_column(df_clean)
    df_temp_summer = loader.filter_summer(df_event)
    df_summer = df_temp_summer["temperature_2m_max"].to_list()

    df_pair = fetcher.call_fetcher_functions(settings.OOS_START, settings.OOS_END)

    return df_summer, df_pair
def run_models():
    df_summer, df_pair = fetch_data()
    buckets = create_buckets(settings.LOWER_BOUND,settings.UPPER_BOUND)

    gaussian_prob_fn = lambda low, high: gaussian_probability(df_summer, low, high)[0]
    kde_prob_fn = lambda low, high: kde_estimate(df_summer, low, high)

    bayesian_factory = lambda day: (lambda low, high: posterior_probability(df_summer, day, df_pair, low, high))

    prob_matrix_gauss, correct_indices_gauss = run_eval(lambda day: gaussian_prob_fn, buckets, df_pair)
    prob_matrix_kde, correct_indices_kde = run_eval(lambda day: kde_prob_fn, buckets, df_pair)
    prob_matrix_bayes, correct_indices_bayes = run_eval(bayesian_factory, buckets, df_pair)

    brier_gauss = brier_score(prob_matrix_gauss, correct_indices_gauss)
    brier_kde = brier_score(prob_matrix_kde, correct_indices_kde)
    brier_bayes = brier_score(prob_matrix_bayes, correct_indices_bayes)

    log_loss_gauss = log_loss(prob_matrix_gauss, correct_indices_gauss)
    log_loss_kde = log_loss(prob_matrix_kde, correct_indices_kde)
    log_loss_bayes = log_loss(prob_matrix_bayes, correct_indices_bayes)

    kde_v_gauss_brier  = skill_score(brier_kde, brier_gauss)
    bayes_v_gauss_brier = skill_score(brier_bayes, brier_gauss)
    bayes_v_kde_brier = skill_score(brier_bayes, brier_kde)

    kde_v_gauss_log  = skill_score(log_loss_kde, log_loss_gauss)
    bayes_v_gauss_log = skill_score(log_loss_bayes,log_loss_gauss)
    bayes_v_kde_log = skill_score(log_loss_bayes, log_loss_kde)


    guessed_prob_gauss = get_guessed_prob(prob_matrix_gauss,correct_indices_gauss)
    guessed_prob_kde = get_guessed_prob(prob_matrix_kde,correct_indices_kde)
    guessed_prob_bayes = get_guessed_prob(prob_matrix_bayes,correct_indices_bayes)

    data_gauss = calculate_buckets(guessed_prob_gauss)
    data_kde = calculate_buckets(guessed_prob_kde)
    data_bayes = calculate_buckets(guessed_prob_bayes)

    scores = [
        ("Gaussian", brier_gauss, log_loss_gauss),
        ("KDE", brier_kde, log_loss_kde),
        ("Bayesian", brier_bayes, log_loss_bayes),
    ]

    print("\n=== Scores ===")
    print(f"{'Model':<10}{'Brier':>10}{'LogLoss':>10}")
    print("-" * 30)
    for name, b, ll in scores:
        print(f"{name:<10}{b:>10.3f}{ll:>10.3f}")

    skill_scores = [
        ("KDE vs Gauss (Brier)", kde_v_gauss_brier),
        ("Bayes vs Gauss (Brier)", bayes_v_gauss_brier),
        ("Bayes vs KDE (Brier)", bayes_v_kde_brier),
        ("KDE vs Gauss (LogLoss)", kde_v_gauss_log),
        ("Bayes vs Gauss (LogLoss)", bayes_v_gauss_log),
        ("Bayes vs KDE (LogLoss)", bayes_v_kde_log),
    ]

    print("\n=== Skill Scores ===")
    print(f"{'Comparison':<25}{'Score':>10}")
    print("-" * 35)
    for name, s in skill_scores:
        print(f"{name:<25}{s:>10.3f}")

    calibration = [
        ("Gaussian", data_gauss),
        ("KDE", data_kde),
        ("Bayesian", data_bayes),
    ]

    print("\n=== Calibration ===")
    for name, data in calibration:
        print(f"\n{name}")
        print(f"{'Bucket':<8}{'Pred':>10}{'Obs':>10}{'N':>8}")
        print("-" * 36)
        for bucket, pred, obs, n in data:
            print(f"{bucket:<8}{pred:>10.3f}{obs:>10.3f}{n:>8}")


def run_experiment():
    fetch_data()
    run_models()


# Source - https://stackoverflow.com/q/419163
# Posted by Devoted, modified by community. See post 'Timeline' for change history
# Retrieved 7/24/2026, License - CC BY-SA 4.0

if __name__ == "__main__":
   run_experiment()
