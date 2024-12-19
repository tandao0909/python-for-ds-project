import os
import time
from typing import Any

from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.linear_model._base import LinearModel
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np
import pandas as pd

from constants import TRAIN_PATH, TARGET_COLUMN, BENCHMARK_DIRPATH

BENCHMARK_PATH = os.path.join(BENCHMARK_DIRPATH, "linear_benchmark.csv")
MODEL_DICT: dict[str, LinearModel] = {
    "Linear Regression": LinearRegression(),
    "Lasso": Lasso(),
    "Ridge": Ridge(),
    "Elastic Net": ElasticNet(),
}
FINE_TUNE_DICT: dict[str, dict[str, list[Any]]] = {
    "Lasso": {"alpha": [0.01, 0.1, 1.0, 10, 100]},
    "Ridge": {"alpha": [0.01, 0.1, 1.0, 10, 100]},
    "Elastic Net": {
        "alpha": [0.01, 0.1, 1.0, 10, 100],
        "l1_ratio": [0.01, 0.1, 1.0],
    },
}


def benchmark_linear_model(
    y_true: pd.Series,
    y_pred: np.ndarray,
    num_features: int,
    train_time: float,
    model_name: str,
    note: str = "",
) -> None:
    rmse = mean_squared_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)

    n = len(y_true)
    k = num_features + 1  # number of features + intercept
    rss = np.sum((y_true - y_pred) ** 2)

    aic = n * np.log(rss / n) + 2 * k
    bic = n * np.log(rss / n) + k * np.log(n)
    adjusted_r2 = 1 - ((1 - r2) * (n - 1) / (n - k - 1))
    benchmark_df = pd.DataFrame(
        {
            "rmse": [rmse],
            "r2": [r2],
            "aic": [aic],
            "bic": [bic],
            "adjusted_r2": [adjusted_r2],
            "train_time(second)": [train_time],
            "model_name": [model_name],
            "note": [note],
        },
    )
    try:
        exist_benchmark = pd.read_csv(BENCHMARK_PATH)
    except pd.errors.EmptyDataError:
        exist_benchmark = None
    benchmark_df = (
        benchmark_df
        if exist_benchmark is None
        else pd.concat([exist_benchmark, benchmark_df], ignore_index=True)
    )
    benchmark_df.to_csv(BENCHMARK_PATH, index=False)


def train_default_linear_models(X: pd.DataFrame, y: pd.Series) -> None:
    for model_name, model in MODEL_DICT.items():
        start_time = time.time()
        model.fit(X, y)
        end_time = time.time()
        benchmark_linear_model(
            y_true=y,
            y_pred=model.predict(X),
            num_features=X.shape[1],
            train_time=end_time - start_time,
            model_name=model_name,
            note="Using default parameters",
        )


def fine_tune_linear_models(X: pd.DataFrame, y: pd.Series):
    # There is really no way to fine tune LR, so we skip it
    for model_name, param_dict in FINE_TUNE_DICT.items():
        grid_search = GridSearchCV(MODEL_DICT[model_name], param_dict)
        start_time = time.time()
        grid_search.fit(X, y)
        end_time = time.time()
        best_params = grid_search.best_params_
        best_model = grid_search.best_estimator_
        benchmark_linear_model(
            y_true=y,
            y_pred=best_model.predict(X),
            num_features=X.shape[1],
            train_time=end_time - start_time,
            model_name=model_name,
            note=f"Fine tune, best params is {best_params}",
        )


def train_linear_models(
    X: pd.DataFrame, y: pd.Series, default: bool = True, fine_tune: bool = True
):
    if default or fine_tune:
        # Clear all content in the benchmark file
        with open(BENCHMARK_PATH, "w") as file:
            pass
    if default:
        print("Train linear models using default parameters")
        train_default_linear_models(X, y)
    if fine_tune:
        print("Fine tune linear models")
        fine_tune_linear_models(X, y)
    print(f"See the benchmark of linear models at {BENCHMARK_PATH}")

if __name__ == "__main__":
    data = pd.read_csv(TRAIN_PATH)
    X = data.drop(TARGET_COLUMN, axis=1)
    y = data[TARGET_COLUMN]
    train_linear_models(X, y)
