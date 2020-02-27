"""This module provides view functions for miscellaneous endpoints."""

# pylint: disable=wrong-import-order


from fastapi import APIRouter
from starlette.responses import JSONResponse
from typing import Text

from projects.src.project_management import ProjectManager
from projects.src.utils import system_stat


router = APIRouter()  # pylint: disable=invalid-name


@router.get('/stat', tags=['miscellaneous'])
def stat() -> JSONResponse:
    """Get statistics of resources usage.
    Returns:
        starlette.responses.JSONResponse
    """

    project_manager = ProjectManager()

    return JSONResponse(dict(
        projects=project_manager.running_projects_stat(),
        system=system_stat()
    ))


@router.get('/healthcheck', tags=['miscellaneous'])
def healthcheck() -> Text:
    """Get healthcheck.
    Returns:
        Text: OK
    """

    return 'OK'
