"""This model contains view functions of default group."""

# pylint: disable=wrong-import-order

from fastapi import APIRouter
from http import HTTPStatus
from starlette.responses import PlainTextResponse

router = APIRouter()  # pylint: disable=invalid-name


@router.get('/healthcheck')
def healthcheck() -> PlainTextResponse:
    """Get healthcheck.
    Returns:
        starlette.responses.PlainTextResponse
    """

    return PlainTextResponse(content='OK', status_code=HTTPStatus.OK)
