"""This is entrypoint module for the service: FastAPI application is defined here."""

# pylint: disable=wrong-import-order
# pylint: disable=invalid-name

from fastapi import FastAPI
from http import HTTPStatus
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response
from starlette.requests import Request

from common.utils import build_error_response, ModelDoesNotExistError
from deploy.src import config
from deploy.src.deployments import DeployManager, DeploymentNotFoundError, InvalidDeploymentType
from deploy.src.routers import default, deployments

app = FastAPI()  # pylint: disable=invalid-name
app.setup()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['GET', 'POST', 'PUT', 'DELETE']
)

app.include_router(default.router)
app.include_router(deployments.router)


@app.on_event('startup')
def init() -> None:
    """Init on application startup"""

    config.create_workspace_dir()
    config.load_gcp_config_env_vars()
    deploy_manager = DeployManager()
    deploy_manager.check_and_update_deployments_statuses()


@app.middleware('http')
async def before_and_after_request(request: Request, call_next) -> Response:
    """Process requests.
    Args:
        request {starlette.requests.Request): input request
        call_next {function}: callback function which invokes request
    Returns:
        starlette.responses.Response
    """
    # pylint: disable=broad-except
    try:
        response = await call_next(request)

    except (DeploymentNotFoundError, InvalidDeploymentType) as e:
        return build_error_response(HTTPStatus.NOT_FOUND, e)

    except ModelDoesNotExistError as e:
        return build_error_response(HTTPStatus.NOT_FOUND, e)

    except Exception as e:
        return build_error_response(HTTPStatus.INTERNAL_SERVER_ERROR, e)

    return response
