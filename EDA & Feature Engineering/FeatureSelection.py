import numpy as np
import pandas as pd
from collections import Counter
from sklearn.feature_selection import VarianceThreshold, SelectKBest, mutual_info_regression
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.feature_selection import SelectFromModel
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from typing import List, Set

class FeatureSelector:
    def __init__(self, X: pd.DataFrame, y: pd.Series, variance_threshold: float = 0.1, k_best: int = 5, top_k_mi: int = 7):
        """
        Initialize the feature selector with the dataset and feature selection parameters.
        
        :param X: The feature matrix (pd.DataFrame).
        :param y: The target variable (pd.Series).
        :param variance_threshold: Threshold for VarianceThreshold method to remove low variance features.
        :param k_best: Number of top features to select using SelectKBest (based on Mutual Information).
        :param top_k_mi: Number of top features to select based on Mutual Information.
        """
        self.X = X
        self.y = y
        self.variance_threshold = variance_threshold
        self.k_best = k_best
        self.top_k_mi = top_k_mi
        self.features_selected: List[Set[str]] = []

    def variance_threshold_selection(self) -> Set[str]:
        """
        Apply VarianceThreshold to remove features with low variance.
        
        :return: A set of selected feature names.
        """
        selector = VarianceThreshold(threshold=self.variance_threshold)
        selector.fit_transform(self.X)
        selected_features = set(self.X.columns[selector.get_support()])
        self.features_selected.append(selected_features)
        return selected_features

    def select_k_best(self) -> Set[str]:
        """
        Apply SelectKBest with Mutual Information to select the top k features.
        
        :return: A set of selected feature names.
        """
        selector = SelectKBest(mutual_info_regression, k=self.k_best).fit(self.X, self.y)
        selected_features = set(self.X.columns[selector.get_support()])
        self.features_selected.append(selected_features)
        return selected_features

    def mutual_information_selection(self) -> Set[str]:
        """
        Compute Mutual Information scores and select the top features based on the scores.
        
        :return: A set of selected feature names.
        """
        mi = mutual_info_regression(self.X, self.y)

        # Normalize the scores for comparison
        mi_normalized = mi / mi.max()

        # Create a DataFrame to store the scores
        feature_scores = pd.DataFrame({
            'Feature': self.X.columns,
            'Mutual Information': mi_normalized
        })

        # Sort features by Mutual Information in descending order
        feature_scores = feature_scores.sort_values(by='Mutual Information', ascending=False)

        # Select the top_k features based on Mutual Information
        top_features = set(feature_scores.head(self.top_k_mi)['Feature'].tolist())
        self.features_selected.append(top_features)
        return top_features

    def grid_search_feature_selection(self) -> Set[str]:
        """
        Use GridSearchCV to optimize hyperparameters of a RandomForestRegressor, and select features based on feature importance.
        
        :return: A set of selected feature names.
        """
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [None, 10, 20],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4]
        }

        rf = RandomForestRegressor(random_state=42)

        grid_search = GridSearchCV(estimator=rf, param_grid=param_grid, cv=5, scoring='neg_mean_squared_error', verbose=2, n_jobs=-1)
        grid_search.fit(self.X, self.y)

        best_model_grid = grid_search.best_estimator_

        pipe = make_pipeline(StandardScaler(), SelectFromModel(estimator=best_model_grid), LinearRegression())
        pipe.fit(self.X, self.y)
        selected_features = set(self.X.columns[pipe.named_steps['selectfrommodel'].get_support()])
        self.features_selected.append(selected_features)
        return selected_features

    def randomized_search_feature_selection(self) -> Set[str]:
        """
        Use RandomizedSearchCV to optimize hyperparameters of a RandomForestRegressor, and select features based on feature importance.
        
        :return: A set of selected feature names.
        """
        param_dist = {
            'n_estimators': np.arange(50, 201, 50),
            'max_depth': [None, 10, 20, 30],
            'min_samples_split': np.arange(2, 11),
            'min_samples_leaf': np.arange(1, 5)
        }

        rf = RandomForestRegressor(random_state=42)

        random_search = RandomizedSearchCV(estimator=rf, param_distributions=param_dist, n_iter=20, cv=5, scoring='neg_mean_squared_error', random_state=42, n_jobs=-1)
        random_search.fit(self.X, self.y)

        best_model_random = random_search.best_estimator_

        pipe = make_pipeline(StandardScaler(), SelectFromModel(estimator=best_model_random), LinearRegression())
        pipe.fit(self.X, self.y)
        selected_features = set(self.X.columns[pipe.named_steps['selectfrommodel'].get_support()])
        self.features_selected.append(selected_features)
        return selected_features

    def combine_selected_features(self) -> List[str]:
        """
        Combine selected features from all methods and count the frequency of occurrence.
        
        :return: A list of final selected features that appeared in two or more methods.
        """
        feature_counter = Counter([feature for feature_set in self.features_selected for feature in feature_set])

        # Get the features that appeared the most across methods
        final_selected_features = [feature for feature, count in feature_counter.items() if count >= 2]  # Appears in 2 or more methods
        return final_selected_features

    def fit(self) -> List[str]:
        """
        Run the entire feature selection process and return the final selected features.
        
        :return: A list of final selected feature names.
        """
        print("Running VarianceThreshold...")
        self.variance_threshold_selection()
        
        print("Running SelectKBest...")
        self.select_k_best()
        
        print("Running Mutual Information...")
        self.mutual_information_selection()
        
        print("Running GridSearchCV...")
        self.grid_search_feature_selection()
        
        print("Running RandomizedSearchCV...")
        self.randomized_search_feature_selection()
        
        print("Combining selected features...")
        final_features = self.combine_selected_features()
        return final_features