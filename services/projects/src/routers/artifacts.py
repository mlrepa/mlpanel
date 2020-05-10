"""This module provides view functions for artifacts endpoints."""

# pylint: disable=wrong-import-order

from fastapi import APIRouter
from http import HTTPStatus
import os
import requests
from starlette.responses import JSONResponse
from starlette.requests import Request
from typing import Dict, Text

from common.types import StrEnum
from common.utils import error_response, is_model
from projects.src.project_management import ProjectManager
from projects.src.utils import log_request


router = APIRouter()  # pylint: disable=invalid-name


class ArtifactType(StrEnum):
    """Artifact type enum."""

    FILE = 'File'
    FOLDER = 'Folder'
    MODEL = 'Model'


def get_artifact_type(root_uri: Text, artifact: Dict) -> ArtifactType:
    """Get artifact type - one of File, Folder and Model.
    Args:
        root_uri {Text} -- absolute path to artifacts location
        artifact {Dict} -- artifact dictionary:
                    {
                        "path": "<path>",
                        "is_dir": true|false,
                        "file_size": "<size of file in bytes"   # optional,
                    }
    Returns:
        ArtifactType -- type of artifact
    """

    if artifact.get('is_dir') is False:
        return ArtifactType.FILE

    if is_model(os.path.join(root_uri, artifact.get('path'))):
        return ArtifactType.MODEL

    return ArtifactType.FOLDER


@router.get('/artifacts', tags=['artifacts'])
def list_artifacts(request: Request, project_id: int, run_id: Text) -> JSONResponse:
    """Get artifacts list.
    Args:
        project_id {int}: project id
        run_id {int}: run_id
    Returns:
        starlette.responses.JSONResponse
    """

    log_request(request, {
        'project_id': project_id,
        'run_id': run_id
    })

    project_manager = ProjectManager()
    url = project_manager.get_internal_tracking_uri(project_id)
    runs_resp = requests.get(
        url=f'{url}/api/2.0/preview/mlflow/artifacts/list?run_id={run_id}'
    )

    if runs_resp.status_code != HTTPStatus.OK:
        return error_response(
            http_response_code=runs_resp.status_code,
            message=runs_resp.json().get('message')
        )

    runs = runs_resp.json()
    root_uri = runs.get('root_uri')
    files = runs.get('files', [])

    runs_list = []

    for i, file in enumerate(files):

        runs_resp = requests.get(
            url=f'{url}/api/2.0/preview/mlflow/runs/get?run_id={run_id}',
        )

        run = runs_resp.json()
        run_info = run.get('run', {}).get('info', {})
        experiment_id = run_info.get('experiment_id')

        runs_list.append({
            'id': f'{project_id}{experiment_id}{run_id}{i}',
            'project_id': project_id,
            'experiment_id': experiment_id,
            'run_id': run_id,
            'type': str(get_artifact_type(root_uri, file)),
            'creation_timestamp': run_info.get('start_time'),
            'root_uri': root_uri,
            'path': file.get('path')
        })

    return JSONResponse(runs_list)
