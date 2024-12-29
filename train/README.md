# Data

The input are two files [housing_train.csv](../data/housing_train.csv) and [housing_test.csv](../data/housing_test.csv). Note that these 2 files hasn't standard scaled

# Rerun the training

```bash

# Install required dependencies
pip install -r requirements.txt

# Run training script
python3 train.py
```

# Rerun the evaluation

After running the training step, the result will be stored at [evaluate/](./benchmark/) directory. Because the metrics to evaluate the best parameters needed to be considered by human, you need to manually input them at this step.

Change the `MODEL_DICT` at [evaluate.py](./evaluate.py).

Then you can
```bash
# Run the evaluation
python3 evaluate.py
```