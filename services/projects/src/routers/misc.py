"""This module provides view functions for miscellaneous endpoints."""

# pylint: disable=wrong-import-order


from fastapi import APIRouter
from starlette.responses import JSONResponse
from starlette.requests import Request
from typing import Text

from projects.src.project_management import ProjectManager
from projects.src.utils import system_stat, log_request


router = APIRouter()  # pylint: disable=invalid-name


@router.get('/stat', tags=['miscellaneous'])
def stat(request: Request) -> JSONResponse:
    """Get statistics of resources usage.
    Returns:
        starlette.responses.JSONResponse
    """

    log_request(request)

    project_manager = ProjectManager()

    return JSONResponse(dict(
        projects=project_manager.running_projects_stat(),
        system=system_stat()
    ))


@router.get('/healthcheck', tags=['miscellaneous'])
def healthcheck(request: Request) -> Text:
    """Get healthcheck.
    Returns:
        Text: OK
    """

    log_request(request)

    return 'OK'
