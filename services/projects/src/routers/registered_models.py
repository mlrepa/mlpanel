"""This module provides view functions for registered models endpoints."""

# pylint: disable=wrong-import-order
# pylint: disable=ungrouped-imports

from fastapi import APIRouter, Form
from http import HTTPStatus
import requests
from starlette.responses import JSONResponse
from typing import Optional, Text

from projects.src.project_management import ProjectManager
from projects.src.routers.utils import get_model_versions, filter_model_versions, \
    check_if_project_and_model_exist
from common.utils import error_response, is_model, ModelDoesNotExistError


router = APIRouter()  # pylint: disable=invalid-name


@router.get('/registered-models', tags=['registered-models'])
def list_models(project_id: int) -> JSONResponse:
    """Get models list.
    Args:
        project_id {int}: project id
    Returns:
        starlette.responses.JSONResponse
    """

    project_manager = ProjectManager()
    url = project_manager.get_tracking_uri(project_id)
    resp = requests.get(f'{url}/api/2.0/preview/mlflow/registered-models/list')
    registered_models = []

    for model in resp.json().get('registered_models_detailed', []):

        registered_models.append({
            'id': model.get('registered_model', {}).get('name'),
            'project_id': project_id,
            'creation_timestamp': model.get('creation_timestamp'),
            'last_updated_timestamp': model.get('last_updated_timestamp')
        })

    return JSONResponse(registered_models)


@router.post('/registered-models', tags=['registered-models'])
def register_model(
        project_id: int,
        name: Text = Form(...),
        source: Text = Form(...),
        run_id: Text = Form(...)
) -> JSONResponse:
    """Register model.
    Args:
        project_id {int}: project id
        name {Text}: model name
        source {Text}: path to model package
        run_id {Text}: run id
    Returns:
        starlette.responses.JSONResponse
    """

    project_manager = ProjectManager()
    if not is_model(source):
        raise ModelDoesNotExistError(f'Model {source} does not exist or is not MLflow model')

    url = project_manager.get_tracking_uri(project_id)
    requests.post(
        url=f'{url}/api/2.0/preview/mlflow/registered-models/create',
        json={'name': name}
    )
    requests.post(
        url=f'{url}/api/2.0/preview/mlflow/model-versions/create',
        json={
            'name': name,
            'source': source,
            'run_id': run_id
        }
    )
    model_resp = requests.post(
        url=f'{url}/api/2.0/preview/mlflow/registered-models/get-details',
        json={'registered_model': {'name': name}}
    )
    registered_model_detailed = model_resp.json().get('registered_model_detailed', {})
    model = {
        'id': name,
        'project_id': project_id,
        'creation_timestamp': registered_model_detailed.get('creation_timestamp'),
        'last_updated_timestamp': registered_model_detailed.get('last_updated_timestamp')
    }

    return JSONResponse(model, HTTPStatus.CREATED)


@router.get('/registered-models/{model_id}', tags=['registered-models'])
def get_model(model_id: Text, project_id: int) -> JSONResponse:
    """Get model.

    Args:
        model_id {Text}: model id (name)
        project_id {int}: project id
    Returns:
        starlette.responses.JSONResponse
    """

    project_manager = ProjectManager()
    url = project_manager.get_tracking_uri(project_id)
    model_resp = requests.post(
        url=f'{url}/api/2.0/preview/mlflow/registered-models/get-details',
        json={'registered_model': {'name': model_id}}
    )

    if model_resp.status_code != HTTPStatus.OK:
        return error_response(
            http_response_code=model_resp.status_code,
            message=model_resp.json().get('message')
        )

    registered_model_detailed = model_resp.json().get('registered_model_detailed', {})
    model = {
        'id': registered_model_detailed.get('registered_model', {}).get('name'),
        'project_id': project_id,
        'creation_timestamp': registered_model_detailed.get('creation_timestamp'),
        'last_updated_timestamp': registered_model_detailed.get('last_updated_timestamp')
    }

    return JSONResponse(model)


@router.delete('/registered-models/{model_id}', tags=['registered-models'])
def delete_model(model_id: Text, project_id: int) -> JSONResponse:
    """Delete model.
    Args:
        model_id {Text}: model id (name)
        project_id {int}: project id
    Returns:
        starlette.responses.JSONResponse
    """

    project_manager = ProjectManager()
    url = project_manager.get_tracking_uri(project_id)
    model_resp = requests.delete(
        url=f'{url}/api/2.0/preview/mlflow/registered-models/delete',
        json={'registered_model': {'name': model_id}}
    )

    if model_resp.status_code != HTTPStatus.OK:
        return error_response(
            http_response_code=model_resp.status_code,
            message=model_resp.json().get('message')
        )

    return JSONResponse({'model_id': model_id})


@router.get('/model-versions', tags=['model-versions'])
def list_model_versions(project_id: int, model_id: Optional[Text] = None) -> JSONResponse:
    """Get model versions list.
    Args:
        project_id {int}: project id
        model_id {Text}: model id (name)
    Returns:
        starlette.responses.JSONResponse
    """

    model_versions = get_model_versions(project_id)

    if model_id is not None:

        check_if_project_and_model_exist(project_id, model_id)
        model_versions = filter_model_versions(model_versions, model_id)

    versions = []

    for version_info in model_versions:

        model_version = version_info.get('model_version', {})
        version_number = model_version.get('version')
        model_id = model_version.get('registered_model', {}).get('name')
        versions.append({
            'id': model_id + version_number,
            'model_id': model_id,
            'project_id': project_id,
            'version': version_number,
            'creation_timestamp': version_info.get('creation_timestamp'),
            'last_updated_timestamp': version_info.get('last_updated_timestamp'),
            'run_id': version_info.get('run_id'),
            'model_uri': version_info.get('source')
        })

    return JSONResponse(versions)


@router.get('/model-versions/{version}', tags=['model-versions'])
def get_model_version(version: Text, project_id: int, model_id: Text) -> JSONResponse:
    """Get model versions list.
    Args:
        project_id {int}: project id
        model_id {Text}: model id (name)
    Returns:
        starlette.responses.JSONResponse
    """

    check_if_project_and_model_exist(project_id, model_id)
    model_versions = filter_model_versions(get_model_versions(project_id), model_id)

    for version_info in model_versions:
        model_version = version_info.get('model_version', {})
        version_number = model_version.get('version')

        if version_number == version:

            return JSONResponse({
                'id': version_number,
                'model_id': model_version.get('registered_model', {}).get('name'),
                'project_id': project_id,
                'version': version_number,
                'creation_timestamp': version_info.get('creation_timestamp'),
                'last_updated_timestamp': version_info.get('last_updated_timestamp'),
                'run_id': version_info.get('run_id'),
                'model_uri': version_info.get('source')
            })

    return error_response(
        http_response_code=HTTPStatus.NOT_FOUND,
        message=f'Version {version} of model {model_id} in project {project_id} not found'
    )
