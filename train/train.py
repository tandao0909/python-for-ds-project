import pandas as pd

from linear_model import train_linear_models
from tree_model import train_tree_models
from svm_model import train_svm_models
from ensemble_model import train_ensemble_models

from constants import TRAIN_PATH, TARGET_COLUMN


def train_models(
    X: pd.DataFrame, y: pd.Series, default: bool = True, fine_tune: bool = False
):
    train_linear_models(X, y, default=default, fine_tune=fine_tune)
    train_tree_models(X, y, default=default, fine_tune=fine_tune)
    train_svm_models(X, y, default=default, fine_tune=fine_tune)
    train_ensemble_models(X, y, default=default, fine_tune=fine_tune)

if __name__ == "__main__":
    data = pd.read_csv(TRAIN_PATH)
    X = data.drop(TARGET_COLUMN, axis=1)
    y = data[TARGET_COLUMN]
    train_models(X, y, fine_tune=True)
