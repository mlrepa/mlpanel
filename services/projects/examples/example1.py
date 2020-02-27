"""
Example1
"""

import mlflow

mlflow.set_experiment('Default')

with mlflow.start_run():
    mlflow.log_param('p', 12)
    mlflow.log_metric('m', 0.98)