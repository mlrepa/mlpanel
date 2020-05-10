"""
Example3
1) logs parameters, metrics and model to run;
2) logs model to Model Registry
"""

import argparse
import mlflow
from mlflow.sklearn import log_model
import pandas as pd
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC
import tensorflow_data_validation as tfdv


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--C', dest='C', type=float, default=1e5, required=False)
    parser.add_argument('--kernel', dest='kernel', type=str, default='rbf', required=False)

    args = parser.parse_args()

    experiment_name = 'IrisSVC'
    mlflow.set_experiment(experiment_name)

    DATASET = 'data/iris.csv'
    TARGET_LABELED_DATASET = 'data/labeled_iris.csv'
    TARGET_COLUMN = 'species'
    IRIS_STATISTICS = '/tmp/stats.tfdv'

    with mlflow.start_run() as run:
        dataset = pd.read_csv(DATASET)
        dataset[TARGET_COLUMN] = LabelEncoder().fit_transform(dataset[TARGET_COLUMN])
        dataset.to_csv(TARGET_LABELED_DATASET, index=False)

        statistics = tfdv.generate_statistics_from_dataframe(dataset.drop(TARGET_COLUMN, axis=1))

        with open(IRIS_STATISTICS, 'wb') as out_stats:
            out_stats.write(statistics.SerializeToString())

        mlflow.log_artifact(DATASET)
        mlflow.log_artifact(TARGET_LABELED_DATASET)
        mlflow.log_artifact(IRIS_STATISTICS)

        train, test = train_test_split(dataset, test_size=0.2, random_state=42)

        X_train = train.drop(TARGET_COLUMN, axis=1).astype('float32')
        y_train = train[TARGET_COLUMN].astype('int32')

        X_test = test.drop(TARGET_COLUMN, axis=1).astype('float32')
        y_test = test[TARGET_COLUMN].astype('int32')

        svc_model = SVC(C=args.C, kernel=args.kernel)

        # Create an instance of Logistic Regression Classifier and fit the data.
        svc_model.fit(X_train, y_train)

        mlflow.log_params(svc_model.get_params())

        prediction = svc_model.predict(X_test)

        f1 = f1_score(y_test, prediction, average='macro')

        mlflow.log_metric('f1', f1)

        log_model(svc_model, 'model')

        mlflow.register_model(f'runs:/{run.info.run_uuid}/model', f'{experiment_name}Model')
