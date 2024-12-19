# Data

The input are two files [housing_train.csv](../data/housing_train.csv) and [housing_test.csv](../data/housing_test.csv). These 2 files hasn't been standard scaled. Hence the pipeline would involve
- Standard scale the data
- Train it using linear, tree-based, ensemble models
- Benchmark the default parameters
- Fine tune and also benchmark
- Finally, consider the best model