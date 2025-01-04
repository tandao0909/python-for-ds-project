import os
from pathlib import Path
from typing import Any

import pandas as pd

from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.linear_model._base import LinearModel

from constants import TRAIN_PATH, TARGET_COLUMN, BENCHMARK_DIRPATH
from utils import train_default_models, fine_tune_models, preprocess_data

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


def train_linear_models(
    X: pd.DataFrame, y: pd.Series, default: bool = True, fine_tune: bool = True
):
    if default or fine_tune:
        Path(BENCHMARK_PATH).parent.mkdir(parents=True, exist_ok=True)
        # Clear all content in the benchmark file
        with open(BENCHMARK_PATH, "w") as file:
            pass
    if default:
        print("Train linear models using default parameters")
        train_default_models(X, y, model_dict=MODEL_DICT, benchmark_path=BENCHMARK_PATH)
    if fine_tune:
        print("Fine tune linear models")
        fine_tune_models(
            X,
            y,
            finetune_dict=FINE_TUNE_DICT,
            model_dict=MODEL_DICT,
            benchmark_path=BENCHMARK_PATH,
        )
    print(f"See the benchmark of linear models at {BENCHMARK_PATH}")


if __name__ == "__main__":
    data = pd.read_csv(TRAIN_PATH)
    data = preprocess_data(data)
    X = data.drop(TARGET_COLUMN, axis=1)
    y = data[TARGET_COLUMN]
    train_linear_models(X, y)
