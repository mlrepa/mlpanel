"""This module provides view functions for runs endpoints."""

# pylint: disable=wrong-import-order

from fastapi import APIRouter
from http import HTTPStatus
import requests
from starlette.responses import JSONResponse
from starlette.requests import Request
from typing import Text

from common.utils import error_response
from projects.src.project_management import ProjectManager
from projects.src.utils import log_request


router = APIRouter()  # pylint: disable=invalid-name


@router.get('/runs', tags=['runs'])
def list_runs(request: Request, project_id: int, experiment_id: Text) -> JSONResponse:
    """Get runs list.
    Args:
        project_id {int}: project id
        experiment_id {Text}: experiment id
    Returns:
        starlette.responses.JSONResponse
    """

    log_request(request)

    project_manager = ProjectManager()
    url = project_manager.get_internal_tracking_uri(project_id)
    resp = requests.post(
        url=f'{url}/api/2.0/preview/mlflow/runs/search',
        json={'experiment_ids': [experiment_id]}
    )

    if resp.status_code != HTTPStatus.OK:
        return error_response(
            http_response_code=resp.status_code,
            message=resp.json().get('message')
        )

    runs = resp.json().get('runs', [])

    for run in runs:
        run['id'] = run.get('info', {}).get('run_id')

    return JSONResponse(runs)


@router.get('/runs/{run_id}', tags=['runs'])
def get_run(request: Request, run_id: Text, project_id: int) -> JSONResponse:
    """Get run.
    Args:
        run_id {Text}: run id
        project_id {int}: project id
    Returns:
        starlette.responses.JSONResponse
    """

    log_request(request)

    project_manager = ProjectManager()
    url = project_manager.get_internal_tracking_uri(project_id)
    resp = requests.get(
        url=f'{url}/api/2.0/preview/mlflow/runs/get?run_id={run_id}',
    )

    if resp.status_code != HTTPStatus.OK:
        return error_response(
            http_response_code=resp.status_code,
            message=resp.json().get('message')
        )

    run = resp.json().get('run')
    run['id'] = run.get('info', {}).get('run_id')
    return JSONResponse(run)


@router.delete('/runs/{run_id}', tags=['runs'])
def delete_run(request: Request, run_id: Text, project_id: int) -> JSONResponse:
    """Delete run.
    Args:
        run_id {Text}: run id
        project_id {int}: project id
    Returns:
        starlette.responses.JSONResponse
    """

    log_request(request, {
        'project_id': project_id,
        'run_id': run_id
    })

    project_manager = ProjectManager()
    url = project_manager.get_internal_tracking_uri(project_id)
    resp = requests.post(
        url=f'{url}/api/2.0/preview/mlflow/runs/delete',
        json={'run_id': run_id}
    )

    if resp.status_code != HTTPStatus.OK:
        return error_response(
            http_response_code=resp.status_code,
            message=resp.json().get('message')
        )

    return JSONResponse({'run_id': run_id})
