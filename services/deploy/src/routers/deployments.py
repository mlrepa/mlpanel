"""This model contains view functions for deployments endpoints"""

# pylint: disable=wrong-import-order

from fastapi import APIRouter, Form
from http import HTTPStatus
from starlette.responses import JSONResponse, Response
from typing import Text

from common.utils import error_response, is_model, ModelDoesNotExistError
from deploy.src import config
from deploy.src.deployments import DeployManager
from deploy.src.deployments import DeploymentNotFoundError

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
    if not is_model(model_uri):
        raise ModelDoesNotExistError(f'Model {model_uri} does not exist or is not MLflow model')

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
            message=response.json().message()
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
