# Comparacion Exhaustiva de Rendimientos (Test Data)

| Modelo                    |      MAE |     RMSE |        R2 |   Error_Relativo_% |
|:--------------------------|---------:|---------:|----------:|-------------------:|
| GradientBoostingRegressor | 0.392468 | 0.495285 |  0.973287 |            15.3738 |
| LinearRegression          | 0.38121  | 0.577922 |  0.963629 |            10.0418 |
| Ridge                     | 0.411079 | 0.581207 |  0.963215 |            10.709  |
| Lasso                     | 0.377227 | 0.583576 |  0.962914 |            10.1341 |
| RandomForestRegressor     | 0.509395 | 0.593635 |  0.961625 |            17.1828 |
| ElasticNet                | 1.38881  | 1.65204  |  0.702796 |            38.3408 |
| DummyRegressor            | 3.82702  | 4.73083  | -1.43718  |           172.972  |