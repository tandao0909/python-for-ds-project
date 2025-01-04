import os
from pathlib import Path
from typing import Any

import pandas as pd

from sklearn.tree import DecisionTreeRegressor

from constants import TRAIN_PATH, TARGET_COLUMN, BENCHMARK_DIRPATH
from utils import train_default_models, fine_tune_models, preprocess_data

BENCHMARK_PATH = os.path.join(BENCHMARK_DIRPATH, "tree_benchmark.csv")
MODEL_DICT: dict[str, Any] = {"Tree": DecisionTreeRegressor()}
FINE_TUNE_DICT: dict[str, dict[str, list[Any]]] = {
    "Tree": {
        "max_depth": [None, 10, 20, 30, 40, 50],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
        "max_features": [None, "auto", "sqrt", "log2"],
        "criterion": ["squared_error", "friedman_mse", "absolute_error", "poisson"],
        "splitter": ["best", "random"],
        "min_weight_fraction_leaf": [0.0, 0.1, 0.2],
        "max_leaf_nodes": [None, 10, 20, 30, 40, 50],
        "min_impurity_decrease": [0.0, 0.01, 0.1],
    }
}


def train_tree_models(
    X: pd.DataFrame, y: pd.Series, default: bool = True, fine_tune: bool = True
):
    if default or fine_tune:
        Path(BENCHMARK_PATH).parent.mkdir(parents=True, exist_ok=True)
        # Clear all content in the benchmark file
        with open(BENCHMARK_PATH, "w") as file:
            pass
    if default:
        print("Train tree-based models using default parameters")
        train_default_models(X, y, model_dict=MODEL_DICT, benchmark_path=BENCHMARK_PATH)
    if fine_tune:
        print("Fine tune tree-based models")
        fine_tune_models(
            X,
            y,
            finetune_dict=FINE_TUNE_DICT,
            model_dict=MODEL_DICT,
            benchmark_path=BENCHMARK_PATH,
        )
    print(f"See the benchmark of tree-based models at {BENCHMARK_PATH}")


if __name__ == "__main__":
    data = pd.read_csv(TRAIN_PATH)
    data = preprocess_data(data)
    X = data.drop(TARGET_COLUMN, axis=1)
    y = data[TARGET_COLUMN]
    train_tree_models(X, y)
