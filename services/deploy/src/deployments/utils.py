"""This module provides auxiliary classes and functions for deploy"""

# pylint: disable=wrong-import-order

import requests
from typing import Text


def mlflow_model_predict(host: Text, port: int, data: Text) -> requests.Response:
    """Predict data on served mlflow model.
    Args:
        host {Text}: host address
        port {int}: port number
        data {Text}: data to predict
    Returns:
        requests.Response
    """

    predict_url = f'http://{host}:{port}/invocations'
    predict_resp = requests.post(
        url=predict_url,
        headers={'Content-Type': 'application/json; format=pandas-records'},
        data=data
    )
    return predict_resp
