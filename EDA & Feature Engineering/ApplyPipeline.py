import pandas as pd
from HousingPipeline import create_pipeline, DataClean

class HousingDataProcessor:
    def __init__(self, api_key, shapefile_path, target_col, drop_na_cols, input_cols, cols_to_impute):
        self.api_key = api_key
        self.shapefile_path = shapefile_path
        self.target_col = target_col
        self.drop_na_cols = drop_na_cols
        self.input_cols = input_cols
        self.cols_to_impute = cols_to_impute
        self.data_cleaner = DataClean(
            api_key=self.api_key,
            target_col=self.target_col,
            drop_na_cols=self.drop_na_cols,
            input_cols=self.input_cols,
            cols_to_impute=self.cols_to_impute
        )
        self.num_pipeline = create_pipeline(shapefile_path=self.shapefile_path)

    def load_data(self, file_path, sep='\t'):
        self.housing = pd.read_csv(file_path, sep=sep)
        print("Data loaded successfully.")

    def clean_data(self):
        self.housing_cleaned = self.data_cleaner.fit_transform(self.housing)
        print("Data cleaning complete.")

    def prepare_data(self):
        self.housing_prepared, self.train_set_scaled, self.test_set_scaled = self.num_pipeline.fit_transform(
            self.housing_cleaned, self.housing_cleaned[self.target_col]
        )
        print("Data preparation complete.")

    def save_data(self, train_file_path='datasets/final_housing_train.csv', test_file_path='datasets/final_housing_test.csv'):
        self.train_set_scaled.to_csv(train_file_path, index=False)
        self.test_set_scaled.to_csv(test_file_path, index=False)
        print(f"Train set scaled saved at: {train_file_path}")
        print(f"Test set scaled saved at: {test_file_path}")

# Usage
processor = HousingDataProcessor(
    api_key="ccc01759bd474d50b77b337c740ed0b7",
    shapefile_path='vietnam_Vietnam_Country_Boundary/extracted_files/vietnam_Vietnam_Country_Boundary.shp',
    target_col='price',
    drop_na_cols=["price", "area"],
    input_cols=['price', 'area', 'car_place', 'facade'],
    cols_to_impute=['bedrooms', 'wc', 'n_floors']
)

processor.load_data('housing.csv')
processor.clean_data()
processor.prepare_data()
processor.save_data()
