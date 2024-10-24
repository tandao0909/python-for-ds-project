import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
import requests
import concurrent.futures

class DataCleaner:
    """
    A class for cleaning and processing datasets, including outlier removal, 
    imputing missing values, address geocoding, and handling feature correlations.
    """

    def __init__(self, api_key: str):
        """
        Initialize the DataCleaner class.

        Parameters:
        - api_key: str. The API key for the OpenCageData geocoding service.
        """
        self.api_key = api_key

    def clean_data(self, df: pd.DataFrame, target_col: str, drop_na_cols: list = [], input_cols: list = [], cols_to_impute: list = []) -> pd.DataFrame:
        """
        Clean the dataset by removing outliers, imputing missing values, 
        and processing addresses into coordinates.

        Parameters:
        - df: pd.DataFrame. The dataset to clean.
        - target_col: str. The target column used for outlier detection.
        - input_cols: list of str. Columns used as input for imputing missing values.
        - cols_to_impute: list of str. Columns where missing values will be imputed.

        Returns:
        - pd.DataFrame. The cleaned dataset.
        """
        df = self.drop_outliers(df, [target_col])

        # Merge 'street' and 'district' columns, handling NaN values
        df['address'] = df['street'].fillna('') + ', ' + df['district'].fillna('')
        df['address'] = df['address'].str.replace('^, |, $', '', regex=True)

        df = self.process_addresses_into_coordinations(df)
        df = df.drop_duplicates()

        drop_na_cols.extend(["latitude", "longitude"])
        df = df.dropna(subset=drop_na_cols)

        df = self.convert_boolean_to_numeric(df)
        input_cols.extend(["latitude", "longitude"])
        df = self.handle_missing_values_by_using_models(df, input_cols, cols_to_impute)
        df = self.drop_outliers(df, df.columns)

        df.hist(bins=50, figsize=(12, 8))
        plt.show()

        answer_for_skewed_cols = input("Are there any skewed columns that need log transformation? (y/n): ")
        if answer_for_skewed_cols.lower() == 'y':
            skewed_cols = input("Enter the names of the skewed columns separated by commas: ").split(',')
            skewed_cols = [col.strip() for col in skewed_cols]  # Remove leading/trailing whitespaces
            
            df = self.apply_log_transformation(df, skewed_cols)

            for col in df.columns:
                if df[col].dtype == float:
                    df[col] = df[col].replace([np.inf, -np.inf], np.nan)

        return df

    def drop_outliers(self, df: pd.DataFrame, columns: list) -> pd.DataFrame:
        """
        Remove outliers from the specified columns based on the interquartile range (IQR).

        Parameters:
        - df: pd.DataFrame. The dataset.
        - columns: list of str. The columns from which to remove outliers.

        Returns:
        - pd.DataFrame. The dataset without outliers.
        """
        for field_name in columns:
            if df[field_name].dtype != 'int64' and df[field_name].dtype != 'float64':
                continue
            Q1 = df[field_name].quantile(0.25)
            Q3 = df[field_name].quantile(0.75)
            IQR = Q3 - Q1
            df = df[(df[field_name] >= (Q1 - 1.5 * IQR)) & (df[field_name] <= (Q3 + 1.5 * IQR))]

        return df

    def process_addresses_into_coordinations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert addresses into latitude and longitude coordinates using the OpenCage API.

        Parameters:
        - df: pd.DataFrame. The dataset with 'address' column.

        Returns:
        - pd.DataFrame. The dataset with added 'latitude' and 'longitude' columns.
        """
        cache = {}

        def get_coordinates(address: str) -> tuple:
            """
            Get the latitude and longitude coordinates of an address.

            Parameters:
            - address: str. The address to geocode.

            Returns:
            - tuple. The latitude and longitude coordinates of the address.
            """
            # Check if the address is already in the cache
            if address in cache:
                return cache[address]
            # Make the API call if not in the cache
            url = f"https://api.opencagedata.com/geocode/v1/json?q={address}&key={self.api_key}"
            try:
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                if data['results']:
                    location = data['results'][0]['geometry']
                    cache[address] = (location['lat'], location['lng'])
                    return location['lat'], location['lng']
                else:
                    cache[address] = (None, None)
                    return None, None
            except requests.RequestException as e:
                print(f"Error fetching data for {address}: {e}")
                return None, None

        # Process addresses concurrently
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(lambda x: get_coordinates(f"{x}, Ho Chi Minh"), df['address']))

        df['latitude'], df['longitude'] = zip(*results)
        return df

    def convert_boolean_to_numeric(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert boolean columns to numeric (0 and 1).

        Parameters:
        - df: pd.DataFrame. The dataset.

        Returns:
        - pd.DataFrame. The dataset with boolean columns converted to numeric.
        """
        for col in df.columns:
            if df[col].dtype == bool:
                df[col] = df[col].astype(int)
        return df

    def handle_missing_values_by_using_models(self, df: pd.DataFrame, input_cols: list = [], cols_to_impute: list = []) -> pd.DataFrame:
        """
        Impute missing values in specified columns using predictive models (KNN, Linear Regression, etc.).

        Parameters:
        - df: pd.DataFrame. The dataset.
        - input_cols: list of str. The input columns for building predictive models.
        - cols_to_impute: list of str. Columns to impute missing values.

        Returns:
        - pd.DataFrame. The dataset with missing values imputed.
        """
        def myWeight(distances: np.array) -> np.array:
            """
            Custom weight function for KNN model.
            
            Parameters:
            - distances: np.array. The distances between points.

            Returns:
            - np.array. The weights for the distances.
            """
            sigma2 = .4
            weights = np.exp(-distances**2 / sigma2)
            return np.where(weights == 0, 1e-5, weights)  # Ensure no zero weights

        models = {
            'knn': KNeighborsClassifier(n_neighbors=12, p=2, weights=myWeight),
            'linear_reg': LinearRegression(),
            'decision_tree': DecisionTreeRegressor(max_depth=5),
            'random_forest': RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
        }

        for col in cols_to_impute:
            print(f"Imputing for column: {col}")
            df_impute = df[input_cols].copy()
            df_impute[col] = df[col]

            df_known = df_impute.dropna(subset=[col])
            df_unknown = df_impute[df_impute[col].isnull()]

            if df_unknown.empty:
                continue

            X_known = df_known.drop(columns=[col])
            y_known = df_known[col]

            X_train, X_test, y_train, y_test = train_test_split(X_known, y_known, test_size=0.2, random_state=42)

            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            best_model = None
            lowest_error = float('inf')

            for model_name, model in models.items():
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
                error = mean_squared_error(y_test, y_pred)

                if error < lowest_error:
                    best_model = model
                    lowest_error = error

                print(f"{model_name} MSE for {col}: {error:.4f}")

            print(f"Best model for {col}: {best_model} with MSE: {lowest_error:.4f}")
            print("-----------------------------------")

            best_model.fit(scaler.fit_transform(X_known), y_known)
            X_unknown_scaled = scaler.transform(df_unknown.drop(columns=[col]))
            y_unknown_pred = best_model.predict(X_unknown_scaled)

            df.loc[df[col].isnull(), col] = y_unknown_pred

        return df

    def apply_log_transformation(self, df: pd.DataFrame, columns: list) -> pd.DataFrame:
        """
        Apply log transformation to skewed columns to reduce the effect of outliers.

        Parameters:
        - df: pd.DataFrame. The dataset.
        - columns: list of str. The columns to apply log transformation.

        Returns:
        - pd.DataFrame. The dataset with log transformation applied to skewed columns.
        """
        def find_skewness(col: pd.Series) -> float:
            """
            Calculate the skewness of a column.

            Parameters:
            - col: pd.Series. The column to calculate skewness.

            Returns:
            - float. The skewness of the column.
            """
            return col.skew()  # Skewness > 0.75 is considered highly skewed

        for col in columns:
            if df[col].dtype == 'int64' or df[col].dtype == 'float64':
                skewness = find_skewness(df[col])
                if skewness > 0.75:
                    df[col] = np.log1p(df[col])

        return df

def del_col(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Delete columns from the dataset.

    Parameters:
    - df: pd.DataFrame. The dataset.
    - columns: list of str. The columns to delete.

    Returns:
    - pd.DataFrame. The dataset with specified columns removed.
    """
    
    for col in df.columns:
        if df[col].dtype == 'object':
            df.drop(columns=[col], axis=1, inplace=True)

    for col in columns:
        df.drop(columns=[col], axis=1, inplace=True)

    return df     