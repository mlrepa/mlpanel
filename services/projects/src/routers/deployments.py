"""This module provides view functions for deployments endpoints."""

# pylint: disable=wrong-import-order

from fastapi import APIRouter, Form
import requests
from starlette.responses import JSONResponse, Response
from typing import Text

from projects.src.routers.utils import get_model_version_uri


router = APIRouter()  # pylint: disable=invalid-name


@router.post('/deployments', tags=['deployments'])
def create_deployment(project_id: int, model_id: Text, version: Text, type: Text) -> JSONResponse:
    """Create deployment.
    Args:
        project_id {int}: project id
        model_id {Text}: model id (name)
        version {Text}: model version
        type {Text}: deployment type
    Returns:
        starlette.responses.JSONResponse
    """
    # pylint: disable=redefined-builtin

    model_uri = get_model_version_uri(project_id, model_id, version)
    deploy_resp = requests.post(
        url='http://deploy:9000/deployments',
        data={
            'project_id': project_id,
            'model_id': model_id,
            'version': version,
            'model_uri': model_uri,
            'type': type
        }
    )

    return JSONResponse(deploy_resp.json(), deploy_resp.status_code)


@router.put('/deployments/{deployment_id}/run', tags=['deployments'])
def run_deployment(deployment_id: int) -> JSONResponse:
    """Run deployment.
    Args:
        deployment_id {int}: deployment id
    Returns:
        starlette.responses.JSONResponse
    """

    deploy_resp = requests.put(f'http://deploy:9000/deployments/{deployment_id}/run')
    return JSONResponse(deploy_resp.json(), deploy_resp.status_code)


@router.put('/deployments/{deployment_id}/stop', tags=['deployments'])
def stop_deployment(deployment_id: int) -> JSONResponse:
    """Stop deployment.
    Args:
        deployment_id {int}: deployment id
    Returns:
        starlette.responses.JSONResponse
    """

    deploy_resp = requests.put(f'http://deploy:9000/deployments/{deployment_id}/stop')
    return JSONResponse(deploy_resp.json(), deploy_resp.status_code)


@router.post('/deployments/{deployment_id}/predict', tags=['deployments'])
def predict(deployment_id: int, data: Text = Form(...)) -> JSONResponse:
    """Predict data on deployment.
    Args:
        deployment_id {int}: deployment id
        data {Text}: data to predict
    Returns:
        starlette.responses.JSONResponse
    """

    deploy_resp = requests.post(
        url=f'http://deploy:9000/deployments/{deployment_id}/predict',
        data={'data': data}
    )
    return JSONResponse(deploy_resp.json(), deploy_resp.status_code)


@router.get('/deployments', tags=['deployments'])
def list_deployments() -> JSONResponse:
    """Get deployments list.
    Returns:
        starlette.responses.JSONResponse
    """

    deployments = requests.get('http://deploy:9000/deployments').json()
    return JSONResponse(deployments)


@router.get('/deployments/{deployment_id}', tags=['deployments'])
def get_deployment(deployment_id: int) -> JSONResponse:
    """Get deployment.
    Args:
        deployment_id {int}: deployment id
    Returns:
        starlette.responses.JSONResponse
    """

    deploy_resp = requests.get(f'http://deploy:9000/deployments/{deployment_id}')
    return JSONResponse(deploy_resp.json(), deploy_resp.status_code)


@router.delete('/deployments/{deployment_id}', tags=['deployments'])
def delete_deployment(deployment_id: int) -> JSONResponse:
    """Delete deployment (mark deployment as deleted).
    Args:
        deployment_id {int}: deployment id
    Returns:
        starlette.responses.JSONResponse
    """

    deploy_resp = requests.delete(f'http://deploy:9000/deployments/{deployment_id}')
    return JSONResponse(deploy_resp.json(), deploy_resp.status_code)


@router.get('/deployments/{deployment_id}/ping')
def ping(deployment_id: int) -> Response:
    """Ping deployment.
    Args:
        deployment_id {int}: deployment id
    Returns:
        starlette.responses.JSONResponse
    """

    deploy_resp = requests.get(f'http://deploy:9000/deployments/{deployment_id}/ping')
    return JSONResponse(deploy_resp.text, status_code=deploy_resp.status_code)
