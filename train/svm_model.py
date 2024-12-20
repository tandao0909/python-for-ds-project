import os
from typing import Any

import pandas as pd

from sklearn.svm import SVR, LinearSVR

from constants import TRAIN_PATH, TARGET_COLUMN, BENCHMARK_DIRPATH
from utils import train_default_models, fine_tune_models

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


def train_svm_models(
    X: pd.DataFrame, y: pd.Series, default: bool = True, fine_tune: bool = True
):
    if default or fine_tune:
        # Clear all content in the benchmark file
        with open(BENCHMARK_PATH, "w") as file:
            pass
    if default:
        print("Train svm models using default parameters")
        train_default_models(X, y, model_dict=MODEL_DICT, benchmark_path=BENCHMARK_PATH)
    if fine_tune:
        print("Fine tune svm models")
        fine_tune_models(
            X,
            y,
            finetune_dict=FINE_TUNE_DICT,
            model_dict=MODEL_DICT,
            benchmark_path=BENCHMARK_PATH,
        )
    print(f"See the benchmark of svm models at {BENCHMARK_PATH}")


if __name__ == "__main__":
    data = pd.read_csv(TRAIN_PATH)
    X = data.drop(TARGET_COLUMN, axis=1)
    y = data[TARGET_COLUMN]
    train_svm_models(X, y)
