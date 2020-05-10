"""This module provides auxiliary classes and functions for deploy"""

# pylint: disable=wrong-import-order

try:
    from google.cloud import storage
    from google.protobuf.json_format import MessageToDict
except ImportError:
    pass

import os
import pandas as pd
from pandas.io.json import build_table_schema
import requests
import time

try:
    import tensorflow_data_validation as tfdv
    from tensorflow_metadata.proto.v0.statistics_pb2 import DatasetFeatureStatisticsList
    from tensorflow_metadata.proto.v0.schema_pb2 import Schema
except ImportError:
    pass

from typing import Dict, NewType, Text, Tuple

from deploy.src import config


if 'DatasetFeatureStatisticsList' not in dir():
    DatasetFeatureStatisticsList = NewType('DatasetFeatureStatisticsList', object)

if 'Schema' not in dir():
    Schema = NewType('Schema', object)


class BadInputDataSchemaError(Exception):
    """Bad input data schema"""


class IncorrectDataError(Exception):
    """Incorrect data"""


TFDV_PANDAS_TYPES = {
    'INT': 'integer',
    'FLOAT': 'number',
    'STRING': 'string',
    'BOOL': 'bool'
}

PANDAS_TFDV_TYPES = {
    pandas_type: tfdv_type
    for tfdv_type, pandas_type in TFDV_PANDAS_TYPES.items()
}


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


def schema_file_exists(schema_file: Text) -> bool:
    """
    Check if schema file exists.
    Args:
        schema_file {Text}: path to schema file
    Returns:
        True if schema file exists, otherwise False
    """

    if schema_file.startswith('gs://'):
        bucket, *schema_file_path_parts = schema_file.strip('gs://').split('/')
        schema_file_path = '/'.join(schema_file_path_parts)
        client = storage.Client()
        bucket = client.get_bucket(bucket)
        schema_file_blob = bucket.blob(schema_file_path)

        return schema_file_blob.exists()

    if os.path.exists(schema_file):
        return True


def get_schema_file_name() -> Text:
    """
    Returns:
        Text: get schema filename
    """

    # TODO (Alex): remove hardcoded schema name
    SCHEMA_NAME = 'stats.tfdv'

    return SCHEMA_NAME


def get_schema_file_path(model_uri: Text) -> Text:
    """
    Get schema file full path.
    Args:
        model_uri {Text}: full path to model
    Returns:
        Text: full path to schema
    """

    schema_path = os.path.join(os.path.dirname(model_uri), get_schema_file_name())

    return schema_path


def download_blob(blob_full_path: Text, destination_file_name: Text) -> None:
    """Downloads a blob from the bucket.
    Args:
        blob_full_path {Text}: full path to blob (gs://<bucket_name>/path/to/file)
        destination_file_name {Text}: destination to download file
    """

    blob_full_path = blob_full_path.strip('gs://')
    bucket_name, *blob_path_parts = blob_full_path.split('/')
    source_blob_name = '/'.join((blob_path_parts))

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(source_blob_name)

    blob.download_to_filename(destination_file_name)


def read_tfdv_statistics(schema_path: Text) -> DatasetFeatureStatisticsList:
    """
    Read TensorFlow data validation (TFDV) statistics.
    Args:
        schema_file {Text}: path to TFDV statistics file
    Returns:
        DatasetFeatureStatisticsList: TFDV statistics
    """

    schema_file = schema_path

    if schema_path.startswith('gs://'):
        dest_folder = f'/tmp/{time.time()}'
        schema_file = os.path.join(dest_folder, get_schema_file_name())
        os.makedirs(os.path.dirname(dest_folder), exist_ok=True)
        download_blob(schema_path, schema_path)

    with open(schema_file, 'rb') as inp_stats:
        string_stats = inp_stats.read()
        statistics = DatasetFeatureStatisticsList().FromString(string_stats)

        return statistics


def tfdv_object_to_dict(tfdv_object: object) -> Dict:
    """
    Convert TFDV object to dictionary.
    Args:
        tfdv_object {DatasetFeatureStatisticsList}: TFDV object
    Returns:
        Dict: dictionary
    """

    return MessageToDict(tfdv_object)


def get_numeric_features_intervals(statistics: DatasetFeatureStatisticsList) -> Dict[str, Tuple]:
    """
    Get numeric features intervals.
    Args:
        statistics {DatasetFeatureStatisticsList}: TFDV statistics.
    Returns:
        Dict[str, Tuple]: dictionary with structure:
            {
                <column_name>: (min_value, max_value)
            }
    """

    statistics_dict = tfdv_object_to_dict(statistics)
    features = statistics_dict['datasets'][0]['features']
    features_intervals = {}

    for ft in features:

        if ft['type'] in ['INT', 'FLOAT']:
            ft_num_stats = ft['numStats']
            ft_interval = (
                ft_num_stats['min'],
                ft_num_stats['max'],
            )
            features_intervals[ft['path']['step'][0]] = ft_interval

    return features_intervals


def get_pandas_df_schema(df: pd.DataFrame) -> Dict[Text, Text]:
    """
    Get dataframe schema using pandas.io.json.build_table_schema.
    Args:
        df {pandas.DataFrame}: dataframe
    Returns:
        Dict[Text, Text]: dictionary with structure:
            {
                <column_name>: <column_type>
            }
    """

    return {f['name']: f['type'] for f in build_table_schema(df, index=False)['fields']}


def tfdv_schema_to_dict(schema: Schema) -> Dict[Text, Text]:
    """
    Convert TFDV schema to flat dictionary.
    Args:
        schema {tensorflow_metadata.proto.v0.schema_pb2.Schema}: TFDV schema
    Returns:
        Dict[Text, Text]: dictionary with structure:
            {
                <column_name>: <column_type>
            }
    """

    raw_schema = MessageToDict(schema)
    schema_dict = {}

    for ft in raw_schema['feature']:
        schema_dict[ft['name']] = TFDV_PANDAS_TYPES[ft.get('type', 'INT')]

    return schema_dict


def load_data(data: Text) -> pd.DataFrame:
    """
    Load data to dataframe from string.
    Args:
        data {Text}: text json string convertible to pandas dataframe, orient=table
    Returns:
        pandas.DataFrame: dataframe
    """

    df = pd.read_json(data, orient='table')

    return df


def tfdv_pandas_schemas_anomalies(tfdv_schema: Schema,
                                  df_schema: Dict[Text, Text]) -> Tuple[bool, Dict]:
    """
    Compare TFDV and pandas schemas - compare and check column names and types.
    Args:
        schema {tensorflow_metadata.proto.v0.schema_pb2.Schema}: TFDV schema
        df_schema {Dict[Text, Text]}: dictified pandas schema
    Returns:
        Tuple[bool, Dict]:
            True if anomalies are detected, otherwise False
            dictionary with structure:
                {
                    <column_name>: {
                        'description': <description>,
                        'severity': 'ERROR',
                        'shortDescription': <short description>,
                        'reason': [{'type': <error_type>,
                                    'shortDescription': <short description>,
                                    'description': <description>}],
                        'path': {'step': [<column_name>]}
                    }
                }
    """

    tfdv_dictified_schema = tfdv_schema_to_dict(tfdv_schema)
    required_columns = set(tfdv_dictified_schema.keys())
    existing_columns = set(df_schema.keys())
    columns = required_columns.union(existing_columns)
    anomalies = {}

    for col in columns:

        if col not in existing_columns:

            anomalies[col] = {
                'description': 'The feature was present in fewer examples than expected.',
                'severity': 'ERROR',
                'shortDescription': 'Column dropped',
                'reason': [{'type': 'FEATURE_TYPE_LOW_FRACTION_PRESENT',
                            'shortDescription': 'Column dropped',
                            'description': 'The feature was present in fewer examples than expected.'}],
                'path': {'step': [col]}
            }

            continue

        if col not in required_columns:

            anomalies[col] = {
                'description': 'New column (column in data but not in schema)',
                'severity': 'ERROR',
                'shortDescription': 'New column',
                'reason': [{'type': 'SCHEMA_NEW_COLUMN',
                            'shortDescription': 'New column',
                            'description': 'New column (column in data but not in schema)'}],
                'path': {'step': [col]}
            }

            continue

        required_type = tfdv_dictified_schema[col]
        real_type = df_schema[col]

        if required_type != real_type:

            short_description = f'Expected data of type: {PANDAS_TFDV_TYPES[required_type]} ' \
                                f'but got {PANDAS_TFDV_TYPES[required_type]}'
            anomalies[col] = {
                'description': '',
                'severity': 'ERROR',
                'shortDescription': short_description,
                'reason': [{'type': 'UNKNOWN_TYPE',
                            'shortDescription': short_description,
                            'description': ''}],
                'path': {'step': [col]}
            }

    return len(anomalies) > 0, anomalies


def data_intervals_anomalies(df: pd.DataFrame,
                             statistics: DatasetFeatureStatisticsList) -> Tuple[bool, Dict]:
    """
    Check if values of each column are between min and max value of the same column from schema.
    Args:
        df {pandas.DataFrame}: dataframe
        statistics {DatasetFeatureStatisticsList}: TFDV statistics
    Returns:
        Tuple[bool, Dict]:
            True if anomalies are detected, otherwise False,
            dictionary with structure:
                {
                    <column_name>: {
                        'description': '',
                        'severity': 'ERROR',
                        'shortDescription': <short description>,
                        'reason': [{'type': 'UNKNOWN_TYPE',
                                    'shortDescription': <short description,
                                    'description': ''}],
                        'path': {'step': [<column_name>]}
                    }
                }
    """

    features_intervals = get_numeric_features_intervals(statistics)
    anomalies = {}

    for col in df.columns:

        if col in features_intervals and df[col].dtype.name != 'object':

            df_col_min, df_col_max = df[col].min().item(), df[col].max().item()
            schema_col_min, schema_col_max = features_intervals[col]

            if type(df_col_min) == type(schema_col_min) and df_col_min < schema_col_min:

                short_description = f'Min value {df_col_min} is less ' \
                                    f'schema min value {schema_col_min}'

                anomalies[col] = {
                    'description': '',
                    'severity': 'ERROR',
                    'shortDescription': short_description,
                    'reason': [{'type': 'UNKNOWN_TYPE',
                                'shortDescription': short_description,
                                'description': ''}],
                    'path': {'step': [col]}
                }

            if type(df_col_max) == type(schema_col_max) and df_col_max > schema_col_max:

                short_description = f'Max value {df_col_max} is more ' \
                                    f'schema max value {schema_col_max}'
                anomalies[col] = {
                    'description': '',
                    'severity': 'ERROR',
                    'shortDescription': short_description,
                    'reason': [{'type': 'UNKNOWN_TYPE',
                                'shortDescription': short_description,
                                'description': ''}],
                    'path': {'step': [col]}
                }

    return len(anomalies) > 0, anomalies


def tfdv_statistics_anomalies(source_statistics: DatasetFeatureStatisticsList,
                              input_statistics: DatasetFeatureStatisticsList) -> Tuple[bool, Dict]:
    """
    Compare two TDFV statistics and return anomalies.
    Args:
        source_statistics {tensorflow_metadata.proto.v0.statistics_pb2.DatasetFeatureStatisticsList}: source statistics
        input_statistics {tensorflow_metadata.proto.v0.statistics_pb2.DatasetFeatureStatisticsList}: input statistics
    Returns:
        Tuple[bool, Dict]:
            True if anomalies are detected, otherwise False,
            dictionary with structure:
            {
                <column_name>: {
                    'description': <description>,
                    'severity': 'ERROR',
                    'shortDescription': <short description>,
                    'reason': [{'type': <error_type>,
                                'shortDescription': <short description>,
                                'description': <description>}],
                    'path': {'step': [<column_name>]}
                }
            }
    """

    schema = tfdv.infer_schema(source_statistics)
    anomalies = tfdv_object_to_dict(
        tfdv.validate_statistics(statistics=input_statistics, schema=schema)
    )
    tfdv_anomalies = anomalies.get('anomalyInfo', {})

    return len(tfdv_anomalies) > 0, tfdv_anomalies


def tfdv_and_additional_anomalies(df: pd.DataFrame,
                                  tfdv_statistics: DatasetFeatureStatisticsList) -> Tuple[bool, Dict]:
    """
    Get TFDV and additional anomalies.
    Args:
        df {pandas.DataFrame}: dataframe
        tfdv_statistics {tensorflow_metadata.proto.v0.statistics_pb2.DatasetFeatureStatisticsList}: TFDV statistics
    Returns:
        Tuple[bool, Dict]:
            True if anomalies are detected, otherwise False,
            dictionary with structure:
            {
                <column_name>: {
                    'description': <description>,
                    'severity': 'ERROR',
                    'shortDescription': <short description>,
                    'reason': [{'type': <error_type>,
                                'shortDescription': <short description>,
                                'description': <description>}],
                    'path': {'step': [<column_name>]}
                }
            }
    """

    df_statistics = tfdv.generate_statistics_from_dataframe(df)
    interval_anomalies_detected = False
    tfdv_anomalies_detected, tfdv_anomalies = tfdv_statistics_anomalies(
        tfdv_statistics, df_statistics
    )
    interval_anomalies = {}

    if len(tfdv_anomalies) > 0:
        tfdv_anomalies_detected = True

    if os.getenv('CHECK_NUMERIC_INTERVALS_ON_PREDICT') == 'true':
        interval_anomalies_detected, interval_anomalies = data_intervals_anomalies(df, tfdv_statistics)

    anomalies_detected = tfdv_anomalies_detected or interval_anomalies_detected
    anomalies = {**tfdv_anomalies, **interval_anomalies}

    return anomalies_detected, anomalies


def pandas_schema_anomalies(df: pd.DataFrame,
                            tfdv_statistics: DatasetFeatureStatisticsList) -> Tuple[bool, Dict]:
    """
    Get dataframe schema anomalies comparing pandas and TFDV schema.
    Args:
        df {pandas.DataFrame}: dataframe
        tfdv_statistics {tensorflow_metadata.proto.v0.statistics_pb2.DatasetFeatureStatisticsList}: TFDV statistics
    Returns:
        Tuple[bool, Dict]:
            True if anomalies are detected, otherwise False,
            dictionary with structure:
                {
                    <column_name>: {
                        'description': <description>,
                        'severity': 'ERROR',
                        'shortDescription': <short description>,
                        'reason': [{'type': <error_type>,
                                    'shortDescription': <short description>,
                                    'description': <description>}],
                        'path': {'step': [<column_name>]}
                    }
                }
    """

    tfdv_schema = tfdv.infer_schema(tfdv_statistics)
    pandas_schema = get_pandas_df_schema(df)

    return tfdv_pandas_schemas_anomalies(tfdv_schema, pandas_schema)


def validate_data(data: Text, schema_file_path: Text) -> Tuple[bool, Dict]:
    """
    Validate data sent for prediction.
    Args:
        data {Text}: json string which can be loaded by panda.read_json(_, orient='split')
        schema_file_path {Text}: path schema file
    Returns:
        Tuple[bool, Dict]:
            True if data is valid, otherwise False,
            dictionary with structure:
            {
                <column_name>: {
                    'description': <description>,
                    'severity': 'ERROR',
                    'shortDescription': <short description>,
                    'reason': [{'type': <error_type>,
                                'shortDescription': <short description>,
                                'description': <description>}],
                    'path': {'step': [<column_name>]}
                }
            }
    """

    if not schema_file_exists(schema_file_path):
        return True, {}

    tfdv_statistics = read_tfdv_statistics(schema_file_path)

    try:
        df = load_data(data)
    except Exception as e:
        raise BadInputDataSchemaError(
            f'Bad input data schema, pandas cannot load data, details: {str(e)}')

    if df.shape[0] >= int(os.getenv('BIG_DATASET_MIN_SIZE', 10e7)):
        validate_func = tfdv_and_additional_anomalies
    else:
        validate_func = pandas_schema_anomalies

    anomalies_detected, anomalies = validate_func(df, tfdv_statistics)

    return not anomalies_detected, anomalies


def predict_data_to_mlflow_data_format(data: Text) -> Text:
    """
    Convert data sent for prediction to format usable by MLflow model server.
    Args:
        data {Text}: json string which can be loaded by panda.read_json(_, orient='split')
    Returns:
        Text: pandas-records string
    """

    df = load_data(data)
    data_in_mlflow_format = str(df.to_numpy().tolist())

    return data_in_mlflow_format


def get_local_deployment_config() -> Dict:

    return {}


def get_gcp_deployment_config() -> Dict:

    return config.Config().get_gcp_config()

