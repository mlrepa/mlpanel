"""
Example2
1) logs parameters, metrics and model to run;
2) logs model to Model Registry
"""

import argparse
import joblib
import numpy as np
import mlflow
from mlflow.sklearn import log_model
import os
from sklearn import datasets
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--C', dest='C', type=float, default=1e5, required=False)
    parser.add_argument('--solver', dest='solver', type=str, default='lbfgs', required=False)

    args = parser.parse_args()

    path = os.path.dirname(os.path.abspath(__file__))
    experiment_name = 'IrisLogreg'
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run() as run:

        # import some data to play with
        iris = datasets.load_iris()

        dataset = os.path.join(path, 'data/iris_data.joblib')

        joblib.dump(iris, dataset)
        # with open(dataset, 'w') as data_f:
        #     json.dump(iris, data_f)

        mlflow.log_artifact(dataset)

        iris_X = iris.data
        iris_y = iris.target

        indices = np.random.permutation(len(iris_X))

        mlflow.log_param('indices', indices.tolist())

        iris_X_train = iris_X[indices[:-10]]
        iris_y_train = iris_y[indices[:-10]]
        iris_X_test = iris_X[indices[-10:]]
        iris_y_test = iris_y[indices[-10:]]

        logreg = LogisticRegression(C=args.C, solver=args.solver, multi_class='multinomial')

        # Create an instance of Logistic Regression Classifier and fit the data.
        logreg.fit(iris_X_train, iris_y_train)

        mlflow.log_params(logreg.get_params())

        prediction = logreg.predict(iris_X_test)

        f1 = f1_score(iris_y_test, prediction, average='macro')

        mlflow.log_metric('f1', f1)

        log_model(logreg, 'model')

        mlflow.register_model(f'runs:/{run.info.run_uuid}/model', f'{experiment_name}Model')
