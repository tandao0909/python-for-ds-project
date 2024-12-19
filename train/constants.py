import os

DATA_DIRPATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
TRAIN_PATH = os.path.join(DATA_DIRPATH, "housing_train.csv")
TEST_PATH = os.path.join(DATA_DIRPATH, "housing_test.csv")
BENCHMARK_DIRPATH = os.path.join(os.path.dirname(__file__), "benchmark")

TARGET_COLUMN = "price"
