import pandas as pd
import folium
from typing import List
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from DataProcessing import DataCleaner, del_col
from Visualize import check_coordinates_in_vietnam, RealEstateVisualizerCluster
from FeatureSelection import FeatureSelector

def process_data(api_key: str, df: pd.DataFrame, target_col: str, drop_na_cols: list, input_cols: list, cols_to_impute: list, unnecessary_columns: list) -> pd.DataFrame:
    """
    Function to process data using DataCleaner and del_col from the DataProcessing module.

    Parameters:
    - api_key (str): API key used to create an instance of DataCleaner.
    - df (pd.DataFrame): The DataFrame containing the data to be processed.
    - target_col (str): The name of the target column for outlier processing.
    - drop_na_cols (list): A list of columns to remove rows with NA values. 
    - input_cols (list): A list of columns to be used for imputing missing values.
    - cols_to_impute (list): A list of columns to impute missing values.

    Returns:
    - pd.DataFrame: The cleaned and processed DataFrame.
    """
    # Create an instance of DataCleaner
    data_cleaner = DataCleaner(api_key)

    # Clean the data: handle outliers, drop rows with NA, and impute missing values
    cleaned_df = data_cleaner.clean_data(
        df=df,
        target_col=target_col,
        drop_na_cols=drop_na_cols,
        input_cols=input_cols,
        cols_to_impute=cols_to_impute
    )

    # Remove unnecessary columns
    processed_df = del_col(cleaned_df, unnecessary_columns)

    # Return the cleaned DataFrame
    return processed_df

def process_and_visualize_real_estate(shapefile_path: str, housing_df: pd.DataFrame, num_clusters: int = 5) -> tuple[folium.Map, pd.DataFrame]:
    """
    Process and visualize real estate data.

    Parameters:
        shapefile_path (str): Path to the shapefile containing Vietnam's territorial boundaries.
        housing_df (pd.DataFrame): Real estate data in the form of a DataFrame.
        num_clusters (int): Number of clusters for data grouping, default is 5.

    Returns:
        folium.Map: A folium map with visualized clusters.
    """
    # Check coordinates within Vietnam's boundaries
    valid_housing_df = check_coordinates_in_vietnam(shapefile_path, housing_df)

    # Initialize RealEstateVisualizerCluster
    visualizer = RealEstateVisualizerCluster(housing_df=valid_housing_df, num_clusters=num_clusters)

    # Perform clustering and prepare data for visualization
    visualizer.fit_kmeans()

    # Create and return a folium map with clusters
    real_estate_map = visualizer.create_map()
    
    # Get the processed DataFrame with cluster information
    processed_df = visualizer.housing

    return real_estate_map, processed_df

def select_important_features(X: pd.DataFrame, y: pd.Series, variance_threshold: float = 0.1, k_best: int = 5, top_k_f_test: int = 7) -> List[str]:
    """
    Use FeatureSelector to select important features.

    Parameters:
        X (pd.DataFrame): Feature matrix.
        y (pd.Series): Target variable.
        variance_threshold (float): Threshold for feature selection using the VarianceThreshold method.
        k_best (int): Number of top features to select using SelectKBest (F-regression).
        top_k_f_test (int): Number of top features to select based on F-test and Mutual Information.

    Returns:
        List[str]: List of important selected features.
    """
    # Create an instance of FeatureSelector
    feature_selector = FeatureSelector(X, y, variance_threshold, k_best, top_k_f_test)
    
    # Run the feature selection process
    selected_features = feature_selector.fit()
    
    return selected_features

def standardize_data(X: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize the data.

    Parameters:
        X (pandas.DataFrame): The input DataFrame.

    Returns:
        pandas.DataFrame: The DataFrame with the data standardized.
    """
    scaler = StandardScaler()
    X_standardized = pd.DataFrame(scaler.fit_transform(X), columns=X.columns, index=X.index)
    return X_standardized

def split_data(X: pd.DataFrame, target_column: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split the data into training and test sets.

    Parameters:
        X (pandas.DataFrame): The input DataFrame.
        target_column (str): The target column to split the data.

    Returns:
        tuple[pandas.DataFrame, pd.DataFrame, pd.DataFrame]: 
        - The full DataFrame after processing.
        - The training set.
        - The test set.
    """
    # Calculate correlations and find the highest correlated column to the target
    corr = X.corr()
    target_corr = corr[target_column].sort_values(ascending=False)
    highest_corr_column = target_corr.index[1]  # The second most correlated column (excluding the target itself)

    # Create a new column with quantile-based categories
    X[f'{highest_corr_column} Category'] = pd.qcut(
        X[highest_corr_column], q=5, labels=False, duplicates='drop'
    )

    # Split the data using stratification on the new category column
    X_train, X_test = train_test_split(
        X, test_size=0.2, stratify=X[f'{highest_corr_column} Category'], random_state=42
    )

    # Remove the temporary category column from all sets
    for subset in (X_train, X_test):
        subset.drop([f'{highest_corr_column} Category'], axis=1, inplace=True)

    X.drop([f'{highest_corr_column} Category'], axis=1, inplace=True)
    return X, X_train, X_test


if __name__ == '__main__':
    # Read dataset
    housing = pd.read_csv('datasets/housing.csv', sep = '\t')

    api_key = "ccc01759bd474d50b77b337c740ed0b7" # api_key to get 'latitude' and 'longitude'
    shapefile_path = 'vietnam_Vietnam_Country_Boundary/extracted_files/vietnam_Vietnam_Country_Boundary.shp' # Path to the shapefile containing the boundary of Vietnam
    
    # Processing data
    processed_df = process_data(
        api_key=api_key,
        df=housing,
        target_col='price', 
        drop_na_cols=['price', 'area'], 
        input_cols=['price', 'area', 'car_place', 'facade'], 
        cols_to_impute=['bedrooms', 'wc', 'n_floors'],
        unnecessary_columns=['facade']
    )

    # Process and visualize real estate
    cluster_map, processed_df = process_and_visualize_real_estate(
        shapefile_path=shapefile_path,
        housing_df=processed_df,
        num_clusters=5
    )

    # Display the cluster map
    cluster_map.save("foliumVisualizationPrice.html")

    # Select important features based on 'price'
    features = processed_df.drop(columns='price')
    target = processed_df['price']
    selected_features = select_important_features(features, target)
    X_filtered = processed_df[selected_features]

    # Standardize the selected features for better scaling
    X_filtered_standardized = standardize_data(X_filtered)

    # Combine the standardized features with the target column 'price'
    X_final_with_price = pd.concat([X_filtered_standardized, target], axis=1)

    # Split the data into train set, test set and save to CSV files
    df_processed, df_train, df_test = split_data(X_final_with_price, target_column='price')
    df_train.to_csv('datasets/housing_train.csv', index=False)
    df_test.to_csv('datasets/housing_test.csv.csv', index=False)
