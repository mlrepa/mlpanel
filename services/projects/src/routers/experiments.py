"""This module provides view functions for experiments endpoints."""

# pylint: disable=wrong-import-order

from fastapi import APIRouter, Form
from http import HTTPStatus
import requests
from starlette.responses import JSONResponse, RedirectResponse
from typing import Text

from projects.src.project_management import ProjectManager
from projects.src.utils import get_utc_timestamp
from common.utils import error_response

router = APIRouter()  # pylint: disable=invalid-name


@router.get('/experiments', tags=['experiments'])
def list_experiments(project_id: int) -> JSONResponse:
    """Get experiments list.
    Args:
        project_id {int}: project id
    Returns:
        starlette.responses.JSONResponse
    """
    project_manager = ProjectManager()
    url = project_manager.get_tracking_uri(project_id)
    resp = requests.get(
        url=f'{url}/api/2.0/preview/mlflow/experiments/list'
    )
    experiments = []

    for exp in resp.json().get('experiments'):

        experiment_id = exp.get('experiment_id')
        runs_resp = requests.get(
            f'{url}/api/2.0/preview/mlflow/runs/search?experiment_ids=[{experiment_id}]'
        )
        runs = runs_resp.json().get('runs', [])
        creation_time = ''
        last_update_time = ''

        """
        if corresponding tags are empty then fields:
            * creation_time = start_time of the first run;
            * last_update_time = end_time of the last run.
        """
        if len(runs) > 0:
            creation_time = runs[len(runs) - 1].get('info', {}).get('start_time')
            last_update_time = runs[0].get('info', {}).get('end_time')

        tags = {tag['key']: tag['value'] for tag in exp.get('tags', [])}
        experiments.append({
            'id': experiment_id,
            'user_id': tags.get('user_id', ''),
            'name': exp.get('name'),
            'artifact_location': exp.get('artifact_location'),
            'lifecycle_stage': exp.get('lifecycle_stage'),
            'last_update_time': tags.get('last_update_time', last_update_time),
            'creation_time': tags.get('creation_time', creation_time),
            'description': tags.get('mlflow.note.content', ''),
            'project_id': tags.get('project_id', project_id)
        })

    return JSONResponse(experiments)


@router.post('/experiments', tags=['experiments'])
def create_experiment(
        project_id: int,
        user_id: Text = Form(''),
        name: Text = Form(''),
        description: Text = Form('')
) -> JSONResponse:
    """Create experiment
    Args:
        project_id {int}: project id
        user_id {Text}: user id (name)
        name {Text}: experiment name
        description {Text}: experiment description
    Returns:
        starlette.responses.JSONResponse
    """

    project_manager = ProjectManager()
    url = project_manager.get_tracking_uri(project_id)
    creation_resp = requests.post(
        url=f'{url}/api/2.0/preview/mlflow/experiments/create',
        json={'name': name}
    )
    creation_json = creation_resp.json()
    experiment_id = creation_json.get('experiment_id')

    if creation_resp.status_code != HTTPStatus.OK:
        return error_response(
            http_response_code=creation_resp.status_code,
            message=creation_json.get('message')
        )

    utc_timestamp = get_utc_timestamp()
    tags = {
        'mlflow.note.content': description,
        'user_id': user_id,
        'project_id': str(project_id),
        'creation_time': utc_timestamp,
        'last_update_time': utc_timestamp
    }

    for key, value in tags.items():
        requests.post(
            url=f'{url}/api/2.0/preview/mlflow/experiments/set-experiment-tag',
            json={
                'experiment_id': experiment_id,
                'key': key,
                'value': value
            }
        )

    experiment_request = requests.get(
        url=f'{url}/api/2.0/preview/mlflow/experiments/get?experiment_id={experiment_id}'
    )

    experiment = experiment_request.json().get('experiment')
    tags = {tag['key']: tag['value'] for tag in experiment.pop('tags', [])}
    experiment['description'] = tags.get('mlflow.note.content', '')
    experiment['user_id'] = tags.get('user_id', '')
    experiment['project_id'] = tags.get('project_id', '')
    experiment['creation_time'] = tags.get('creation_time', '')
    experiment['last_update_time'] = tags.get('last_update_time', '')

    return JSONResponse(experiment, HTTPStatus.CREATED)


@router.get('/experiments/{experiment_id}', tags=['experiments'])
def get_experiment(experiment_id: Text, project_id: int) -> JSONResponse:
    """Get experiment.
    Args:
        experiment_id {Text}: experiment id
        project_id {int}: project id
    Returns:
        starlette.responses.JSONResponse
    """

    project_manager = ProjectManager()
    url = project_manager.get_tracking_uri(project_id)
    experiment_resp = requests.get(
        url=f'{url}/api/2.0/preview/mlflow/experiments/get?experiment_id={experiment_id}'
    )

    if experiment_resp.status_code != HTTPStatus.OK:
        return error_response(
            http_response_code=experiment_resp.status_code,
            message=experiment_resp.json().get('message')
        )

    experiment = experiment_resp.json().get('experiment')
    experiment_id = experiment.get('experiment_id')
    runs_resp = requests.get(
        f'{url}/api/2.0/preview/mlflow/runs/search?experiment_ids=[{experiment_id}]'
    )
    runs = runs_resp.json().get('runs', [])
    creation_time = ''
    last_update_time = ''

    """
    if corresponding tags are empty then fields:
        * creation_time = start_time of the first run;
        * last_update_time = end_time of the last run.
    """
    if len(runs) > 0:
        creation_time = runs[len(runs) - 1].get('info', {}).get('start_time')
        last_update_time = runs[0].get('info', {}).get('end_time')

    experiment['id'] = experiment.pop('experiment_id')
    tags = {tag['key']: tag['value'] for tag in experiment.pop('tags', [])}
    experiment['description'] = tags.get('mlflow.note.content', '')
    experiment['user_id'] = tags.get('user_id', '')
    experiment['project_id'] = tags.get('project_id', project_id)
    experiment['creation_time'] = tags.get('creation_time', creation_time)
    experiment['last_update_time'] = tags.get('last_update_time', last_update_time)

    return JSONResponse(experiment)


@router.delete('/experiments/{experiment_id}', tags=['experiments'])
def delete_experiment(experiment_id: Text, project_id: int) -> JSONResponse:
    """Delete experiment.
    Args:
        experiment_id {Text}: experiment id
        project_id {int}: project id
    Returns:
        starlette.responses.JSONResponse
    """

    project_manager = ProjectManager()
    url = project_manager.get_tracking_uri(project_id)
    experiment_resp = requests.post(
        url=f'{url}/api/2.0/preview/mlflow/experiments/delete',
        json={'experiment_id': experiment_id}
    )

    if experiment_resp.status_code != HTTPStatus.OK:
        return error_response(
            http_response_code=experiment_resp.status_code,
            message=experiment_resp.json().get('message')
        )

    return JSONResponse({'experiment_id': experiment_id})


# TODO(Alex): remove endpoint
@router.get('/projects/{id}/experiments')
def alt_list_experiments(id: int):

    return RedirectResponse(f'/experiments?project_id={id}')
