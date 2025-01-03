from pathlib import Path
import time
from typing import Any
from joblib import dump

import pandas as pd
import numpy as np

from sklearn.model_selection import GridSearchCV
from sklearn.metrics import (
    root_mean_squared_error,
    r2_score,
    mean_absolute_percentage_error,
    mean_absolute_error,
    explained_variance_score,
)
from sklearn.preprocessing import StandardScaler


def train_default_models(
    X: pd.DataFrame, y: pd.Series, model_dict: dict[str, Any], benchmark_path: str
) -> None:
    """
    Train multiple models with default parameters and benchmark their performance.

    Parameters:
    ----------
    - X (pd.DataFrame): The input features for training the models.
    - y (pd.Series): The target variable for training the models.
    - model_dict (dict[str, Any]): A dictionary where keys are model names and values are model instances.
    - benchmark_path (str): The file path to save the benchmark results.

    Returns:
    --------
    None
    """
    for model_name, model in model_dict.items():
        start_time = time.time()
        model.fit(X, y)
        end_time = time.time()
        benchmark_model(
            y_true=y,
            y_pred=model.predict(X),
            num_features=X.shape[1],
            train_time=end_time - start_time,
            model_name=model_name,
            benchmark_path=benchmark_path,
            note="Using default parameters",
        )


def fine_tune_models(
    X: pd.DataFrame,
    y: pd.Series,
    finetune_dict: dict[str, dict[str, list[Any]]],
    model_dict: dict[str, Any],
    benchmark_path: str,
):
    """
    Fine-tune multiple models and benchmark their performance.

    Parameters:
    ----------
    - X (pd.DataFrame): The input features for training the models.
    - y (pd.Series): The target variable for training the models.
    - finetune_dict (dict[str, dict[str, list[Any]]]): A dictionary where keys are model names and values are parameter grids for GridSearchCV.
    - model_dict (dict[str, Any]): A dictionary where keys are model names and values are model instances.
    - benchmark_path (str): The file path to save the benchmark results.

    Returns:
    --------
    None
    """
    for model_name, param_dict in finetune_dict.items():
        grid_search = GridSearchCV(model_dict[model_name], param_dict)
        start_time = time.time()
        grid_search.fit(X, y)
        end_time = time.time()
        best_params = grid_search.best_params_
        best_model = grid_search.best_estimator_
        benchmark_model(
            y_true=y,
            y_pred=best_model.predict(X),
            num_features=X.shape[1],
            train_time=end_time - start_time,
            model_name=model_name,
            benchmark_path=benchmark_path,
            note=f"Fine tune, best params is {best_params}",
        )


def benchmark_model(
    y_true: pd.Series,
    y_pred: np.ndarray,
    num_features: int,
    train_time: float,
    model_name: str,
    benchmark_path: str,
    note: str = "",
) -> None:
    """
    Evaluate and save model performance metrics.

    This function calculates various performance metrics for a regression model,
    including RMSE, R-squared, AIC, BIC, adjusted R-squared, MAPE, MAE, and explained variance.
    It then saves these metrics along with the training time, model name, and an optional note
    to a CSV file specified by `benchmark_path`.

    Parameters:
    ----------
    - y_true (pd.Series): True target values.
    - y_pred (np.ndarray): Predicted target values.
    - num_features (int): Number of features used in the model, required to calculate AIC and BIC.
    - train_time (float): Time taken to train the model in seconds.
    - model_name (str): Name of the model.
    - benchmark_path (str): Path to the CSV file where benchmark results will be saved.
    - note (str, optional): Additional note to be saved with the benchmark results. Defaults to "".

    Returns:
    --------
    None
    """
    rmse = root_mean_squared_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)

    n = len(y_true)
    k = num_features + 1  # number of features + intercept
    rss = np.sum((y_true - y_pred) ** 2)

    aic = n * np.log(rss / n) + 2 * k
    bic = n * np.log(rss / n) + k * np.log(n)
    adjusted_r2 = 1 - ((1 - r2) * (n - 1) / (n - k - 1))

    mape = mean_absolute_percentage_error(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    explained_variance = explained_variance_score(y_true, y_pred)

    benchmark_df = pd.DataFrame(
        {
            "rmse": [rmse],
            "r2": [r2],
            "aic": [aic],
            "bic": [bic],
            "adjusted_r2": [adjusted_r2],
            "mape": [mape],
            "mae": [mae],
            "explained_variance": [explained_variance],
            "train_time(second)": [train_time],
            "model_name": [model_name],
            "note": [note],
        },
    )
    Path(benchmark_path).parent.mkdir(parents=True, exist_ok=True)
    try:
        exist_benchmark = pd.read_csv(benchmark_path)
    except pd.errors.EmptyDataError:
        exist_benchmark = None
    benchmark_df = (
        benchmark_df
        if exist_benchmark is None
        else pd.concat([exist_benchmark, benchmark_df], ignore_index=True)
    )
    benchmark_df.to_csv(benchmark_path, index=False)


def preprocess_data(
    data: pd.DataFrame, standard_scale: bool = True, columns_to_drop: list[str] = ["id"]
) -> pd.DataFrame:
    """
    Preprocesses the input data by optionally dropping specified columns and applying standard scaling.

    Parameters:
    ----------
    - data (pd.DataFrame): The input data to preprocess.
    - standard_scale (bool): Whether to apply standard scaling to the data. Default is True.
    - columns_to_drop (list[str]): List of column names to drop from the data. Default is ["id"].

    Returns:
    --------
    pd.DataFrame: The preprocessed data.

    Note:
    -----
    If you apply standard scaling, the fitted scaler will be saved in a .joblib file.
    """
    if not columns_to_drop is None:
        data = data.drop(columns=columns_to_drop)
    if standard_scale:
        std_scaler = StandardScaler()
        data = pd.DataFrame(
            std_scaler.fit_transform(data), columns=data.columns, index=data.index
        )
        dump(std_scaler, "standard_scaler.joblib")
    return data
