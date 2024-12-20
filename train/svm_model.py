import os
import time
from typing import Any

import numpy as np
import pandas as pd

from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVR, LinearSVR
from sklearn.metrics import (
    root_mean_squared_error,
    r2_score,
    mean_absolute_percentage_error,
    mean_absolute_error,
    explained_variance_score,
)

from constants import TRAIN_PATH, TARGET_COLUMN, BENCHMARK_DIRPATH

BENCHMARK_PATH = os.path.join(BENCHMARK_DIRPATH, "svm_benchmark.csv")
MODEL_DICT: dict[str, Any] = {
    "Linear": LinearSVR(),
    "Poly": SVR(kernel="poly"),
    "Rbf": SVR(kernel="rbf"),
    "Sigmoid": SVR(kernel="sigmoid"),
}
FINE_TUNE_DICT: dict[str, dict[str, list[Any]]] = {
    "Linear": {
        "C": [0.1, 1, 10, 100, 1000],
        "epsilon": [0.01, 0.1, 1],
    },
    "Poly": {
        "C": [0.1, 1, 10, 100, 1000],
        "epsilon": [0.01, 0.1, 1],
        "degree": [2, 3, 4],
        "coef0": [0.0, 0.1, 0.5, 1.0],
        "gamma": ["scale", "auto"],
    },
    "Rbf": {
        "C": [0.1, 1, 10, 100, 1000],
        "epsilon": [0.01, 0.1, 1],
        "gamma": ["scale", "auto"],
    },
    "Sigmoid": {
        "C": [0.1, 1, 10, 100, 1000],
        "epsilon": [0.01, 0.1, 1],
        "coef0": [0.0, 0.1, 0.5, 1.0],
        "gamma": ["scale", "auto"],
    },
}


def benchmark_svm_model(
    y_true: pd.Series,
    y_pred: np.ndarray,
    train_time: float,
    model_name: str,
    note: str = "",
):
    rmse = root_mean_squared_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    mape = mean_absolute_percentage_error(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    explained_variance = explained_variance_score(y_true, y_pred)
    benchmark_df = pd.DataFrame(
        {
            "rmse": [rmse],
            "r2": [r2],
            "mape": [mape],
            "mae": [mae],
            "explained_variance": [explained_variance],
            "train_time(second)": [train_time],
            "model_name": [model_name],
            "note": [note],
        }
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


def train_default_svm_models(X: pd.DataFrame, y: pd.Series) -> None:
    for model_name, model in MODEL_DICT.items():
        start_time = time.time()
        model.fit(X, y)
        end_time = time.time()
        benchmark_svm_model(
            y_true=y,
            y_pred=model.predict(X),
            train_time=end_time - start_time,
            model_name=model_name,
            note="Using default parameters",
        )


def fine_tune_svm_models(X: pd.DataFrame, y: pd.Series):
    # There is really no way to fine tune LR, so we skip it
    for model_name, param_dict in FINE_TUNE_DICT.items():
        grid_search = GridSearchCV(MODEL_DICT[model_name], param_dict)
        start_time = time.time()
        grid_search.fit(X, y)
        end_time = time.time()
        best_params = grid_search.best_params_
        best_model = grid_search.best_estimator_
        benchmark_svm_model(
            y_true=y,
            y_pred=best_model.predict(X),
            train_time=end_time - start_time,
            model_name=model_name,
            note=f"Fine tune, best params is {best_params}",
        )


def train_svm_models(
    X: pd.DataFrame, y: pd.Series, default: bool = True, fine_tune: bool = True
):
    if default or fine_tune:
        # Clear all content in the benchmark file
        with open(BENCHMARK_PATH, "w") as file:
            pass
    if default:
        print("Train linear models using default parameters")
        train_default_svm_models(X, y)
    if fine_tune:
        print("Fine tune linear models")
        fine_tune_svm_models(X, y)
    print(f"See the benchmark of linear models at {BENCHMARK_PATH}")

if __name__ == "__main__":
    data = pd.read_csv(TRAIN_PATH)
    X = data.drop(TARGET_COLUMN, axis=1)
    y = data[TARGET_COLUMN]
    train_svm_models(X, y)
