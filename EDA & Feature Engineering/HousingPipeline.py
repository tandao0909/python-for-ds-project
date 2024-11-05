import pandas as pd
import os
import numpy as np

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_regression, mutual_info_regression, SelectFromModel
from sklearn.model_selection import train_test_split, GridSearchCV, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.cluster import KMeans

import folium
from folium.plugins import HeatMap
from folium import LinearColormap
from haversine import haversine
from collections import Counter
from typing import List, Set, Tuple

from DataProcessing import DataCleaner, del_col
from Visualize import check_coordinates_in_vietnam, visualize_real_estate_price, visualize__real_estate_clusters, visualize_real_estate_price_heatmap
from FeatureSelection import FeatureSelector


class DataClean(BaseEstimator, TransformerMixin):
    """
    Cleaning and processing datasets, including outlier removal, 
    imputing missing values, address geocoding, and handling feature correlations.
    """
    def __init__(self, api_key: str, target_col: str, drop_na_cols: list = [], input_cols: list = [], cols_to_impute: list = []):
        self.api_key = api_key
        self.target_col = target_col
        self.drop_na_cols = drop_na_cols
        self.input_cols = input_cols
        self.cols_to_impute = cols_to_impute
        self.data_cleaner = DataCleaner(api_key=api_key)
    
    def fit(self, X, y=None):
        # The fit method does not perform any specific actions
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        # Use the clean_data method of DataCleaner
        X = self.data_cleaner.clean_data(
            df=X, 
            target_col=self.target_col, 
            drop_na_cols=self.drop_na_cols, 
            input_cols=self.input_cols, 
            cols_to_impute=self.cols_to_impute
        )
        return X


class DelCol(BaseEstimator, TransformerMixin):
    """
    Delete columns from the dataset.

    Parameters:
    - df: pd.DataFrame. The dataset.
    - columns: list of str. The columns to delete.

    Returns:
    - pd.DataFrame. The dataset with specified columns removed.
    """
    def __init__(self, columns: list):
        self.columns = columns
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = del_col(df=X.copy(), columns=self.columns)
        return X


class CheckCoordinatesInVietnam(BaseEstimator, TransformerMixin):
    """
    Check if the coordinates are in Vietnam

    Parameters:
        shapefile_path (str): The path to the shapefile

    Returns:
        pandas.DataFrame: The DataFrame with the coordinates checked
    """
    def __init__(self, shapefile_path:str):
        self.shapefile_path = shapefile_path

    def fit(self, X, y=None):
        return self
    
    def transform(self, X:pd.DataFrame) -> pd.DataFrame:
        X = check_coordinates_in_vietnam(shapefile_path=self.shapefile_path, housing_df=X)
        return X


class Visualize(BaseEstimator, TransformerMixin):
    """
    Class to visualize the data right after checking the coordinates.
    The data will be saved as HTML files.
    """
    def __init__(self, clusters_map_path: str = 'real_estate_clusters_map.html'):
        self.clusters_map_path = clusters_map_path

    def fit(self, X, y=None):
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        # Visualize Real Estate Clusters
        clusters_map = visualize__real_estate_clusters(X)
        clusters_map.save(self.clusters_map_path)
        
        print(f"Visualizations saved to {self.clusters_map_path}")
        return X

class FeatureSelector(BaseEstimator, TransformerMixin):
    def __init__(self, variance_threshold: float = 0.1, k_best: int = 5, top_k_f_test: int = 7):
        """
        Initialize the feature selector with feature selection parameters.
        
        :param variance_threshold: Threshold for VarianceThreshold method to remove low variance features.
        :param k_best: Number of top features to select using SelectKBest (based on F-regression).
        :param top_k_f_test: Number of top features to select based on F-test and Mutual Information.
        """
        self.variance_threshold = variance_threshold
        self.k_best = k_best
        self.top_k_f_test = top_k_f_test
        self.features_selected: List[Set[str]] = []
        self.final_features: List[str] = []

    def variance_threshold_selection(self, X: pd.DataFrame) -> Set[str]:
        selector = VarianceThreshold(threshold=self.variance_threshold)
        selector.fit_transform(X)
        selected_features = set(X.columns[selector.get_support()])
        self.features_selected.append(selected_features)
        return selected_features

    def select_k_best(self, X: pd.DataFrame, y: pd.Series) -> Set[str]:
        selector = SelectKBest(f_regression, k=self.k_best).fit(X, y)
        selected_features = set(X.columns[selector.get_support()])
        self.features_selected.append(selected_features)
        return selected_features

    def f_test_and_mutual_information(self, X: pd.DataFrame, y: pd.Series) -> Set[str]:
        f_test, p_values = f_regression(X, y)
        mi = mutual_info_regression(X, y)

        # Normalize the scores for comparison
        epsilon = 1e-200
        f_test_normalized = -np.log10(p_values + epsilon)
        f_test_normalized /= f_test_normalized.max()
        mi_normalized = mi / mi.max()

        # Create a DataFrame to store the scores
        feature_scores = pd.DataFrame({
            'Feature': X.columns,
            'F-test': f_test_normalized,
            'Mutual Information': mi_normalized
        })

        feature_scores = feature_scores.sort_values(by='F-test', ascending=False)
        top_features = set(feature_scores.head(self.top_k_f_test)['Feature'].tolist())
        self.features_selected.append(top_features)
        return top_features

    def grid_search_feature_selection(self, X: pd.DataFrame, y: pd.Series) -> Set[str]:
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [None, 10, 20],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4]
        }

        rf = RandomForestRegressor(random_state=42)
        grid_search = GridSearchCV(estimator=rf, param_grid=param_grid, cv=5, scoring='neg_mean_squared_error', verbose=0, n_jobs=-1)
        grid_search.fit(X, y)
        best_model_grid = grid_search.best_estimator_

        pipe = make_pipeline(StandardScaler(), SelectFromModel(estimator=best_model_grid))
        pipe.fit(X, y)
        selected_features = set(X.columns[pipe.named_steps['selectfrommodel'].get_support()])
        self.features_selected.append(selected_features)
        return selected_features

    def randomized_search_feature_selection(self, X: pd.DataFrame, y: pd.Series) -> Set[str]:
        param_dist = {
            'n_estimators': np.arange(50, 201, 50),
            'max_depth': [None, 10, 20, 30],
            'min_samples_split': np.arange(2, 11),
            'min_samples_leaf': np.arange(1, 5)
        }

        rf = RandomForestRegressor(random_state=42)
        random_search = RandomizedSearchCV(estimator=rf, param_distributions=param_dist, n_iter=20, cv=5, scoring='neg_mean_squared_error', random_state=42, n_jobs=-1)
        random_search.fit(X, y)
        best_model_random = random_search.best_estimator_

        pipe = make_pipeline(StandardScaler(), SelectFromModel(estimator=best_model_random))
        pipe.fit(X, y)
        selected_features = set(X.columns[pipe.named_steps['selectfrommodel'].get_support()])
        self.features_selected.append(selected_features)
        return selected_features

    def combine_selected_features(self) -> List[str]:
        feature_counter = Counter([feature for feature_set in self.features_selected for feature in feature_set])
        final_selected_features = [feature for feature, count in feature_counter.items() if count >= 2]
        return final_selected_features

    def fit(self, X: pd.DataFrame, y: pd.Series = None):
        self.variance_threshold_selection(X)
        self.select_k_best(X, y)
        self.f_test_and_mutual_information(X, y)
        self.grid_search_feature_selection(X, y)
        self.randomized_search_feature_selection(X, y)
        self.final_features = self.combine_selected_features()
        print(f"Final selected features: {self.final_features}")
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if not self.final_features:
            raise RuntimeError("You must fit the transformer before transforming data!")
        return X[self.final_features]

    
class StandardizeData(BaseEstimator, TransformerMixin):
    """
    Standardize the data

    Returns:
        pandas.DataFrame: The DataFrame with the data standardized
    """
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self
    
    def transform(self, X:pd.DataFrame) -> pd.DataFrame:
        """
        Standardize the data

        Parameters:
            X (pandas.DataFrame): The input DataFrame

        Returns:
            pandas.DataFrame: The DataFrame with the data standardized
        """
        scaler = StandardScaler()
        X = pd.DataFrame(scaler.fit_transform(X), columns=X.columns, index=X.index)
        return X


class SplitData(BaseEstimator, TransformerMixin):
    """
    Split the data into training and test sets

    Parameters:
        target_column (str): The target column to split the data

    Returns:
        pandas.DataFrame: The training and test sets
    """
    def __init__(self, target_column:str):
        self.target_column = target_column

    def fit(self, X, y=None):
        return self
    
    def transform(self, X:pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split the data into training and test sets

        Parameters:
            X (pandas.DataFrame): The input DataFrame

        Returns:
            tuple[pandas.DataFrame, pandas.DataFrame]: The training and test sets
        """

        corr = X.corr()
        target_corr = corr[self.target_column].sort_values(ascending=False)
        highest_corr_column = target_corr.index[1]

        X[f'{highest_corr_column} Category'] = pd.qcut(X[highest_corr_column], q=5, labels=False, duplicates='drop')
        # qcut: Quantile-based discretization function. Discretize variable into equal-sized buckets based on rank or based on sample quantiles.
        X_train, X_test = train_test_split(X, test_size=0.2, stratify=X[f'{highest_corr_column} Category'], random_state=42)

        for set in (X_train, X_test):
            set.drop([f'{highest_corr_column} Category'], axis=1, inplace=True)

        X.drop([f'{highest_corr_column} Category'], axis=1, inplace=True)
        return X, X_train, X_test

# Pipeline for numerical attributes
def create_pipeline(shapefile_path):
    return Pipeline(steps=[
        ('del_col', DelCol(columns=['facade'])),
        ('check_coordinates_in_vietnam', CheckCoordinatesInVietnam(shapefile_path=shapefile_path)),
        ('visualize', Visualize(clusters_map_path='VisualizationCluster.html')),
        ('feature_selector', FeatureSelector(variance_threshold=0.1, k_best=5, top_k_f_test=7)),
        ('standardize', StandardizeData()),
        ('split_data', SplitData(target_column='price'))
    ])