import os
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from sklearn.svm import SVR
from sklearn.linear_model import Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import ExtraTreesRegressor

from constants import TEST_PATH, TARGET_COLUMN, BENCHMARK_DIRPATH
from utils import train_default_models

MODEL_DICT: dict[str, Any]  = {
    "Ridge": Ridge(),
    "Tree": DecisionTreeRegressor(
        criterion='poisson',
        max_depth=50,
        max_features=None,
        max_leaf_nodes=50,
        min_impurity_decrease=0.0,
        min_samples_leaf=4,
        min_samples_split=2,
        min_weight_fraction_leaf=0.0,
        splitter='best'
    ),
    "Rbf": SVR(kernel="rbf"),
    "Extra Tree": ExtraTreesRegressor(n_jobs=-1),
}
BENCHMARK_PATH = os.path.join(BENCHMARK_DIRPATH, "evaluate.csv")
MODEL_DIRPATH = os.path.join(os.path.dirname(__file__), "models")

def evaluate_models(
    X: pd.DataFrame, y: pd.Series
):
    Path(BENCHMARK_PATH).parent.mkdir(parents=True, exist_ok=True)

    # Clear all content in the benchmark file
    with open(BENCHMARK_PATH, "w") as file:
        pass
    print("Evaluate models using the fine tuned parameters.")
    train_default_models(X, y, model_dict=MODEL_DICT, benchmark_path=BENCHMARK_PATH)
    print(f"See the evaluation results at {BENCHMARK_PATH}")

def save_models(X: pd.DataFrame, y: pd.Series):
    Path(MODEL_DIRPATH).mkdir(parents=True, exist_ok=True)
    for model_name, model in MODEL_DICT.items():
        model.fit(X, y)
        model_path = os.path.join(MODEL_DIRPATH, f"{model_name}.joblib")
        joblib.dump(model, model_path)
    print(f"Models are saved at {MODEL_DIRPATH}.")

if __name__ == "__main__":
    data = pd.read_csv(TEST_PATH)
    X = data.drop(TARGET_COLUMN, axis=1)
    y = data[TARGET_COLUMN]
    evaluate_models(X, y)
    save_models(X, y)
