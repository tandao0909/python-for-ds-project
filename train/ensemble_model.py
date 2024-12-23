import os
from pathlib import Path
from typing import Any

import pandas as pd

from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor,
    AdaBoostRegressor,
    BaggingRegressor,
    ExtraTreesRegressor,
)
from catboost import CatBoostRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from constants import TRAIN_PATH, TARGET_COLUMN, BENCHMARK_DIRPATH
from utils import train_default_models, fine_tune_models

BENCHMARK_PATH = os.path.join(BENCHMARK_DIRPATH, "ensemble_benchmark.csv")
MODEL_DICT: dict[str, Any] = {
    "Random Forest": RandomForestRegressor(n_jobs=-1),
    "Gradient Boosting": GradientBoostingRegressor(),
    "AdaBoost": AdaBoostRegressor(),
    "Bagging": BaggingRegressor(n_jobs=-1),
    "Extra Tree": ExtraTreesRegressor(n_jobs=-1),
    "CatBoost": CatBoostRegressor(),
    "XGBoost": XGBRegressor(),
    "LightGBM": LGBMRegressor(n_jobs=-1),
}
FINE_TUNE_DICT: dict[str, dict[str, list[Any]]] = {
    "Random Forest": {
        "n_estimators": [100, 200, 300],
        "max_depth": [None, 10, 20, 30, 40, 50],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
        "max_features": [None, "auto", "sqrt", "log2"],
        "criterion": ["squared_error", "friedman_mse", "absolute_error", "poisson"],
        "splitter": ["best", "random"],
        "min_weight_fraction_leaf": [0.0, 0.1, 0.2],
        "max_leaf_nodes": [None, 10, 20, 30, 40, 50],
        "min_impurity_decrease": [0.0, 0.01, 0.1],
    },
    "Gradient Boosting": {
        "n_estimators": [100, 200, 300],
        "max_depth": [None, 10, 20, 30, 40, 50],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
        "max_features": [None, "auto", "sqrt", "log2"],
        "criterion": ["squared_error", "friedman_mse", "absolute_error", "poisson"],
        "splitter": ["best", "random"],
        "min_weight_fraction_leaf": [0.0, 0.1, 0.2],
        "max_leaf_nodes": [None, 10, 20, 30, 40, 50],
        "min_impurity_decrease": [0.0, 0.01, 0.1],
        "subsample": [0.8, 0.9, 1.0],
    },
    "AdaBoost": {
        "n_estimators": [50, 100, 200],
        "learning_rate": [0.01, 0.1, 1.0],
    },
    "Bagging": {
        "n_estimators": [10, 20, 50],
        "max_samples": [0.5, 0.7, 1.0],
        "max_features": [0.5, 0.7, 1.0],
    },
    "Extra Tree": {
        "n_estimators": [100, 200, 300],
        "max_depth": [None, 10, 20, 30, 40, 50],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
        "max_features": [None, "auto", "sqrt", "log2"],
        "criterion": ["squared_error", "friedman_mse", "absolute_error", "poisson"],
        "splitter": ["best", "random"],
        "min_weight_fraction_leaf": [0.0, 0.1, 0.2],
        "max_leaf_nodes": [None, 10, 20, 30, 40, 50],
        "min_impurity_decrease": [0.0, 0.01, 0.1],
    },
    "CatBoost": {
        "iterations": [100, 200, 300],
        "depth": [4, 6, 10],
        "learning_rate": [0.01, 0.1, 0.2],
        "l2_leaf_reg": [1, 3, 5],
    },
    "XGBoost": {
        "n_estimators": [100, 200, 300],
        "max_depth": [3, 5, 7],
        "learning_rate": [0.01, 0.1, 0.2],
        "subsample": [0.8, 0.9, 1.0],
    },
    "LightGBM": {
        "n_estimators": [100, 200, 300],
        "num_leaves": [31, 50, 100],
        "learning_rate": [0.01, 0.1, 0.2],
        "feature_fraction": [0.8, 0.9, 1.0],
    },
}


def train_ensemble_models(
    X: pd.DataFrame, y: pd.Series, default: bool = True, fine_tune: bool = False
):
    if default or fine_tune:
        Path(BENCHMARK_PATH).parent.mkdir(parents=True, exist_ok=True)

        # Clear all content in the benchmark file
        with open(BENCHMARK_PATH, "w") as file:
            pass
    if default:
        print("Train ensemble models using default parameters")
        train_default_models(X, y, model_dict=MODEL_DICT, benchmark_path=BENCHMARK_PATH)
    if fine_tune:
        print("Fine tune ensemble models")
        fine_tune_models(
            X,
            y,
            finetune_dict=FINE_TUNE_DICT,
            model_dict=MODEL_DICT,
            benchmark_path=BENCHMARK_PATH,
        )
    print(f"See the benchmark of ensemble models at {BENCHMARK_PATH}")


if __name__ == "__main__":
    data = pd.read_csv(TRAIN_PATH)
    X = data.drop(TARGET_COLUMN, axis=1)
    y = data[TARGET_COLUMN]
    train_ensemble_models(X, y)
