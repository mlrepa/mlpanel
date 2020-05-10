"""This module provides view functions for projects endpoints."""

# pylint: disable=wrong-import-order
# pylint: disable=ungrouped-imports

from fastapi import APIRouter, Form
from http import HTTPStatus
import requests
from starlette.responses import JSONResponse
from starlette.requests import Request
from typing import Text

from common.utils import error_response
from projects.src.project_management import ProjectManager
from projects.src.utils import log_request

router = APIRouter()  # pylint: disable=invalid-name


@router.get('/projects', tags=['projects'])
def list_projects(request: Request) -> JSONResponse:
    """Get projects list.
    Returns:
        starlette.responses.JSONResponse
    """

    log_request(request)

    project_manager = ProjectManager()
    projects = project_manager.list_projects()
    return JSONResponse(projects)


@router.post('/projects', tags=['projects'])
def create_project(request: Request, name: Text = Form(...),
                   description: Text = Form('')) -> JSONResponse:
    """Create project.
    Args:
        name {Text}: project name
        description {Text}: project description
    Returns:
        starlette.responses.JSONResponse
    """

    log_request(request, {
        'name': name,
        'description': description
    })

    project_manager = ProjectManager()
    project_id = project_manager.create_project(name, description)
    project = project_manager.get_project(project_id)

    return JSONResponse(project, HTTPStatus.CREATED)


@router.get('/projects/{project_id}', tags=['projects'])
def get_project(request: Request, project_id: int) -> JSONResponse:  # pylint: disable=invalid-name,redefined-builtin
    """Get project.
    Args:
        project_id {int}: project id
    Returns:
        starlette.responses.JSONResponse
    """

    log_request(request)

    project_manager = ProjectManager()
    project = project_manager.get_project(project_id)
    return JSONResponse(project)


@router.put('/projects/{project_id}', tags=['projects'])
def update_project(request: Request, project_id: int, name: Text = Form(None),
                   description: Text = Form(None)) -> JSONResponse:
    """Update project.
    Args:
        project_id {int}: project id
        name {Text}: project name
        description {Text}: project description
    Returns:
        starlette.responses.JSONResponse
    """

    log_request(request, {
        'project_id': project_id,
        'name': name,
        'description': description
    })

    project_manager = ProjectManager()
    if name is not None:
        project_manager.update_project_name(project_id, name)

    if description is not None:
        project_manager.update_project_description(project_id, description)

    project = project_manager.get_project(project_id)

    return JSONResponse(project)


@router.delete('/projects/{project_id}', tags=['projects'])
def delete_project(request: Request, project_id: int) -> JSONResponse:  # pylint: disable=invalid-name,redefined-builtin
    """Delete project.
    Args:
        project_id {int}: project id
    Returns:
        starlette.responses.JSONResponse
    """

    log_request(request, {
        'project_id': project_id
    })

    project_manager = ProjectManager()
    project = project_manager.get_project(project_id)
    project_manager.terminate(project_id)
    project_manager.delete_project(project_id)

    return JSONResponse(project, status_code=HTTPStatus.OK)


@router.get('/projects/{project_id}/healthcheck', tags=['projects'])
def project_healthcheck(request: Request, project_id: int) -> JSONResponse:  # pylint: disable=invalid-name,redefined-builtin
    """Get project healthcheck (check if project's tracking server process was started).
    Args:
        project_id {int}: project id
    Returns:
        starlette.responses.JSONResponse
    """

    log_request(request)

    project_manager = ProjectManager()
    project = project_manager.get_project(project_id)
    is_running = project_manager._is_running(project_id)

    if is_running:
        return JSONResponse(project, HTTPStatus.OK)
    else:
        return JSONResponse(project, HTTPStatus.BAD_REQUEST)


@router.put('/projects/{project_id}/run', tags=['projects'])
def run_project(request: Request, project_id: int) -> JSONResponse:  # pylint: disable=invalid-name,redefined-builtin
    """Run project's tracking server.
    Args:
        project_id {int}: project id
    Returns:
        starlette.responses.JSONResponse
    """

    log_request(request, {
        'project_id': project_id
    })

    project_manager = ProjectManager()
    running = project_manager.run(project_id)

    if not running:
        return error_response(
            http_response_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            message='Internal error, tracking server has terminated'
        )

    project = project_manager.get_project(project_id)
    return JSONResponse(project, HTTPStatus.OK)


@router.put('/projects/{project_id}/terminate', tags=['projects'])
def terminate_project(request: Request, project_id: int) -> JSONResponse:  # pylint: disable=invalid-name,redefined-builtin
    """Terminate project's tracking server.
    Args:
        project_id {int}: project id
    Returns:
        starlette.responses.JSONResponse
    """

    log_request(request, {
        'project_id': project_id
    })

    project_manager = ProjectManager()
    project_manager.terminate(project_id)
    project = project_manager.get_project(project_id)

    return JSONResponse(project, HTTPStatus.OK)


@router.put('/projects/{project_id}/archive', tags=['projects'])
def archive(request: Request, project_id: int) -> JSONResponse:  # pylint: disable=invalid-name,redefined-builtin
    """Archive project.
    Args:
        id {int}: project id
    Returns:
        starlette.responses.JSONResponse
    """

    log_request(request, {
        'project_id': project_id
    })

    project_manager = ProjectManager()
    project_manager.terminate(project_id)
    project_manager.archive(project_id)
    project = project_manager.get_project(project_id)

    return JSONResponse(project, HTTPStatus.OK)


@router.put('/projects/{project_id}/restore', tags=['projects'])
def restore(request: Request, project_id: int) -> JSONResponse:  # pylint: disable=invalid-name,redefined-builtin
    """Restore project.
    Args:
        project_id {int}: project id
    Returns:
        starlette.responses.JSONResponse
    """

    log_request(request, {
        'project_id': project_id
    })

    project_manager = ProjectManager()
    project_manager.restore(project_id)
    project = project_manager.get_project(project_id)

    return JSONResponse(project, HTTPStatus.OK)


@router.get('/projects/{project_id}/ping', tags=['projects'])
def ping(request: Request, project_id: int) -> JSONResponse:
    """Ping project's tracking server.
    Args:
        project_id {int}: project id
    Returns:
        starlette.responses.JSONResponse
    """

    log_request(request)

    project_manager = ProjectManager()
    url = project_manager.get_internal_tracking_uri(project_id)
    project = project_manager.get_project(project_id)

    try:
        requests.get(url)
        return JSONResponse(project, HTTPStatus.OK)
    except requests.exceptions.ConnectionError:
        return JSONResponse(project, HTTPStatus.BAD_REQUEST)
