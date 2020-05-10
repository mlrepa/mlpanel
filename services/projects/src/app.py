"""This is entrypoint module for the service: FastAPI application is defined here."""

# pylint: disable=wrong-import-order

from fastapi import FastAPI
from http import HTTPStatus
import json
import psutil
import psycopg2
from starlette.responses import JSONResponse, Response
from starlette.requests import Request

from common.utils import build_error_response
from projects.src.config import Config
from projects.src.project_management import ProjectsDBSchema, BadProjectNameError, \
    ProjectAlreadyExistsError, ProjectIsAlreadyRunningError, ProjectNotFoundError
from projects.src.routers import misc, projects, artifacts, registered_models, experiments, \
    runs, deployments
from projects.src.routers.utils import RegisteredModelNotFoundError

app = FastAPI()  # pylint: disable=invalid-name
app.setup()

app.include_router(projects.router)
app.include_router(experiments.router)
app.include_router(runs.router)
app.include_router(registered_models.router)
app.include_router(misc.router)
app.include_router(artifacts.router)
app.include_router(deployments.router)


conf = Config()
logger = conf.get_logger(__name__)


@app.on_event('startup')
def init() -> None:
    """Init on application startup, create DB if not exists, check active projects"""
    try:

        # TODO: add .create_if_not_exist()
        ProjectsDBSchema()

        # find gost projects (check PIDs) set '-1' if processed stopped|not exists (default)
        # TODO: wrap in method
        connection = psycopg2.connect(
            database=conf.get('PROJECTS_DB_NAME'),
            host=conf.get('DB_HOST'),
            port=conf.get('DB_PORT'),
            user=conf.get('DB_USER'),
            password=conf.get('DB_PASSWORD')
        )
        cursor = connection.cursor()
        cursor.execute(f'SELECT id, pid FROM {ProjectsDBSchema.PROJECTS_TABLE}')

        for project_id, pid in cursor.fetchall():
            if not psutil.pid_exists(pid):
                cursor.execute(
                    f'UPDATE {ProjectsDBSchema.PROJECTS_TABLE} SET pid = -1 WHERE id = %s',
                    (project_id,)
                )
        connection.commit()
        connection.close()

    except Exception as e:  # pylint: disable=invalid-name
        logger.error(e, exc_info=True)


@app.middleware('http')
async def before_and_after_request(request: Request, call_next) -> Response:
    """Process requests.
    Args:
        request {starlette.requests.Request): input request
        call_next {function}: callback function which invokes request
    Returns:
        starlette.responses.Response
    """
    # pylint: disable=too-many-locals,invalid-name,broad-except

    # check DB schema is valid
    # TODO (Alex): rewrite
    # if config.DB_SCHEMA['status'] == 'fail':
    #     return JSONResponse(config.DB_SCHEMA, HTTPStatus.INTERNAL_SERVER_ERROR)

    try:
        response = await call_next(request)

    except (BadProjectNameError, ProjectAlreadyExistsError) as e:
        return build_error_response(HTTPStatus.BAD_REQUEST, e)

    except (ProjectNotFoundError, RegisteredModelNotFoundError) as e:
        return build_error_response(HTTPStatus.NOT_FOUND, e)

    except ProjectIsAlreadyRunningError as e:
        return build_error_response(HTTPStatus.CONFLICT, e)

    except Exception as e:
        logger.error(e, exc_info=True)
        return build_error_response(HTTPStatus.INTERNAL_SERVER_ERROR, e)

    ip = request.headers.get('X-Forwarded-For', request.client.host)
    host = request.client.host.split(':', 1)[0]
    query_params = dict(request.query_params)

    log_params = [
        ('method', request.method),
        ('path', request.url.path),
        ('status', response.status_code),
        ('ip', ip),
        ('host', host),
        ('params', query_params)
    ]

    line = json.dumps(dict(log_params))
    logger.debug(line)
    final_response = response

    if response.headers.get('content-type') == 'application/json':

        body = [b async for b in response.body_iterator]
        content = response.render(b''.join(body))
        json_content = json.loads(content)

        if isinstance(json_content, list):

            sort_key = query_params.get('_sort')
            order = query_params.get('_order')
            start = int(query_params.get('_start', 0))
            end = int(query_params.get('_end', len(json_content)))

            if sort_key is not None:
                json_content = sorted(json_content,
                                      key=lambda e: e[sort_key],
                                      reverse=(order == 'DESC'))

            json_content = json_content[start:end]
            final_response = JSONResponse(json_content)
            final_response.headers['X-Total-Count'] = str(len(json_content))
            final_response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'

        else:
            final_response = JSONResponse(json_content)

    final_response.status_code = response.status_code

    return final_response
