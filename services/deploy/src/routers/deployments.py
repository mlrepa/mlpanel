"""This model contains view functions for deployments endpoints"""

# pylint: disable=wrong-import-order

from fastapi import APIRouter, Form
from http import HTTPStatus
import pandas as pd
import psycopg2
from starlette.responses import JSONResponse, Response

try:
    import tensorflow_data_validation as tfdv
except ImportError:
    pass

from typing import Text

from common.utils import error_response
from deploy.src.config import Config
from deploy.src.deployments.manager import DeploymentNotFoundError, DeployDbSchema, DeployManager
from deploy.src.deployments.utils import get_schema_file_path, read_tfdv_statistics,\
    tfdv_object_to_dict, load_data, schema_file_exists, tfdv_statistics_anomalies,\
    data_intervals_anomalies

router = APIRouter()  # pylint: disable=invalid-name


@router.post('/deployments')
def create_and_run_deployment(
        project_id: int = Form(...),
        model_id: Text = Form(...),
        version: Text = Form(...),
        model_uri: Text = Form(...),
        type: Text = Form(...)  # pylint: disable=redefined-builtin
) -> JSONResponse:
    """Create and run deployment.
    Args:
        project_id {int}: project id
        model_id {Text}: model id (name)
        version {Text}: model version
        model_uri {Text}: path to model package
        type {Text}: deployment type
    Returns:
        starlette.responses.JSONResponse
    """

    deploy_manager = DeployManager()
    deployment_id = deploy_manager.create_deployment(
        project_id, model_id, version, model_uri, type
    )
    return JSONResponse({'deployment_id': str(deployment_id)}, HTTPStatus.ACCEPTED)


@router.put('/deployments/{deployment_id}/run')
def run_deployment(deployment_id: int) -> JSONResponse:
    """Run deployment.
    Args:
        deployment_id {int}: deployment id
    Returns:
        starlette.responses.JSONResponse
    """

    deploy_manager = DeployManager()
    deploy_manager.run(deployment_id=deployment_id)
    return JSONResponse({'deployment_id': str(deployment_id)}, HTTPStatus.OK)


@router.put('/deployments/{deployment_id}/stop')
def stop_deployment(deployment_id: int) -> JSONResponse:
    """Stop deployment.
    Args:
        deployment_id {int}: deployment id
    Returns:
        starlette.responses.JSONResponse
    """

    deploy_manager = DeployManager()
    deploy_manager.stop(deployment_id=deployment_id)
    return JSONResponse({'deployment_id': str(deployment_id)}, HTTPStatus.OK)


@router.post('/deployments/{deployment_id}/predict')
def predict(deployment_id: int, data: Text = Form(...)) -> JSONResponse:
    """Predict data on deployment.
    Args:
        deployment_id {int}: deployment id
        data {Text}: data to predict
    Returns:
        starlette.responses.JSONResponse
    """

    deploy_manager = DeployManager()
    response = deploy_manager.predict(deployment_id=deployment_id, data=data)

    if response.status_code != HTTPStatus.OK:
        return error_response(
            http_response_code=response.status_code,
            message=response.json().get('message')
        )

    return JSONResponse({'prediction': response.text})


@router.get('/deployments')
def list_deployments() -> JSONResponse:
    """Get list of deployments
    Returns:
        starlette.responses.JSONResponse
    """

    deploy_manager = DeployManager()
    deployments = deploy_manager.list()
    return JSONResponse(deployments)


@router.get('/deployments/{deployment_id}')
def get_deployment(deployment_id: int) -> JSONResponse:
    """Get deployment
    Args:
        deployment_id {int}: deployment id
    Returns:
        starlette.responses.JSONResponse
    """

    deploy_manager = DeployManager()
    deployments = deploy_manager.list()

    for deployment in deployments:
        if deployment.get('id') == str(deployment_id):
            return JSONResponse(deployment)

    raise DeploymentNotFoundError(f'Deployment with ID {deployment_id} not found')


@router.delete('/deployments/{deployment_id}')
def delete_deployment(deployment_id: int) -> JSONResponse:
    """Delete deployment (mark as deleted).
    Args:
        deployment_id {int}: deployment id
    Returns:
        starlette.responses.JSONResponse
    """

    deploy_manager = DeployManager()
    deploy_manager.delete(deployment_id=deployment_id)
    return JSONResponse({'deployment_id': str(deployment_id)}, HTTPStatus.OK)


@router.get('/deployments/{deployment_id}/ping')
def ping(deployment_id: int) -> Response:
    """Ping deployment.
    Args:
        deployment_id {int}: deployment id
    Returns:
        starlette.responses.Response
    """

    deploy_manager = DeployManager()
    available = deploy_manager.ping(deployment_id=deployment_id)

    if available:
        return Response(status_code=HTTPStatus.OK)
    else:
        return Response(status_code=HTTPStatus.BAD_REQUEST)


@router.get('/deployments/{deployment_id}/schema')
def get_deployment_data_schema(deployment_id: int) -> JSONResponse:
    """Get deployment data schema.
    Args:
        deployment_id {int}: deployment id
    Returns:
        starlette.responses.JSONResponse
    """

    deploy_manager = DeployManager()
    deployment_schema = deploy_manager.deployment_schema(deployment_id)

    return JSONResponse(deployment_schema)


@router.get('/deployments/{deployment_id}/validation-report')
def get_validation_report(deployment_id: int,
                   timestamp_from: float,
                   timestamp_to: float) -> JSONResponse:

    conf = Config()
    connection = psycopg2.connect(
            database=conf.get('PROJECTS_DB_NAME'),
            host=conf.get('DB_HOST'),
            port=conf.get('DB_PORT'),
            user=conf.get('DB_USER'),
            password=conf.get('DB_PASSWORD')
        )
    cursor = connection.cursor()

    cursor.execute(
        f'SELECT model_uri FROM {DeployDbSchema.DEPLOYMENTS_TABLE} '
        f'WHERE id = {deployment_id}'
    )

    try:
        model_uri = cursor.fetchone()[0]
    except TypeError:
        raise DeploymentNotFoundError(f'Deployment with ID {deployment_id} not found')

    cursor.execute(
        f'SELECT incoming_data FROM {DeployDbSchema.INCOMING_DATA_TABLE} '
        f'WHERE deployment_id = {deployment_id} AND '
        f'     timestamp >= {timestamp_from} AND timestamp <= {timestamp_to}'
    )

    schema_file_path = get_schema_file_path(model_uri)

    if not schema_file_exists(schema_file_path):
        return JSONResponse({})

    tfdv_statistics = read_tfdv_statistics(schema_file_path)
    tfdv_statistics_dict = tfdv_object_to_dict(tfdv_statistics)

    data_batches = cursor.fetchall()
    dataframes = []

    for batch in data_batches:
        df = load_data(batch[0])
        dataframes.append(df)

    if len(dataframes) == 0:
        return JSONResponse({})

    incoming_data_df = pd.concat(dataframes, ignore_index=False)

    """
     Convert object columns to string to avoid errors when trying to generate TFDV
     statistics. If column contains string and numeric values it's type is object, but 
     the column still contains values of different types. And TFDV tries to convert string 
     value to numeric (integer, float) => error 
    """
    object_columns = incoming_data_df.select_dtypes(include='object').columns.tolist()
    incoming_data_df[object_columns] = incoming_data_df[object_columns].astype('str')

    incoming_data_statistics = tfdv.generate_statistics_from_dataframe(incoming_data_df)
    incoming_data_statistics_dict = tfdv_object_to_dict(incoming_data_statistics)

    tfdv_anomalies_detected, tfdv_anomalies = tfdv_statistics_anomalies(
        tfdv_statistics, incoming_data_statistics
    )
    interval_anomalies_detected, interval_anomalies = data_intervals_anomalies(
        incoming_data_df, tfdv_statistics
    )
    anomalies_detected = tfdv_anomalies_detected or interval_anomalies_detected
    anomalies = {**tfdv_anomalies, **interval_anomalies}

    return JSONResponse({
        'timestamp_from': timestamp_from,
        'timestamp_to': timestamp_to,
        'model_statistics': tfdv_statistics_dict,
        'incoming_data_statistics': incoming_data_statistics_dict,
        'anomalies_detected': anomalies_detected,
        'anomalies_info': anomalies
    })
