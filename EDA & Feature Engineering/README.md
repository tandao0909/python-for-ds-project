# Data Description

| Column 1             | Column 2                              |
| -------------------- | ------------------------------------- |
| wc                   | Number of bathrooms                   |
| car_place            | Number of car parking spaces          |
| Cluster              | Cluster identifier                    |
| n_floors             | Number of floors                      |
| bedrooms             | Number of bedrooms                    |
| Distance to center 1 | Distance to the city center           |
| id                   | Unique identifier                     |
| area                 | Area of the property in square meters |
| price                | Price of the property                 |

`Cluster` and `Distance to center 1` are artificially created. `wc`, `bedrooms`, and `n_floors` are imputed using `DataCleaner` class in [DataProcessing.py](./DataProcessing.py).