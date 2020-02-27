"""This is entrypoint module for the service: FastAPI application is defined here."""

# pylint: disable=wrong-import-order

from fastapi import FastAPI
from http import HTTPStatus
import json
import os
import psutil
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, Response
from starlette.requests import Request
from starlette.templating import Jinja2Templates
import sqlite3

from common.utils import build_error_response
from projects.src import config
from projects.src.project_management import BadProjectNameError, \
    ProjectAlreadyExistsError, ProjectIsAlreadyRunningError, ProjectNotFoundError, \
    BadSQLiteTableSchema
from projects.src.routers import misc, projects, artifacts, registered_models, experiments, \
    runs, deployments
from projects.src.routers.utils import RegisteredModelNotFoundError

app = FastAPI()  # pylint: disable=invalid-name
app.setup()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['GET', 'POST', 'PUT', 'DELETE']
)

app.include_router(projects.router)
app.include_router(experiments.router)
app.include_router(runs.router)
app.include_router(registered_models.router)
app.include_router(misc.router)
app.include_router(artifacts.router)
app.include_router(deployments.router)

templates = Jinja2Templates(directory='src/templates')  # pylint: disable=invalid-name


@app.on_event('startup')
def init() -> None:
    """Init on application startup"""
    try:
        config.set_logger()
        projects_db = os.path.join(config.WORKSPACE, config.PROJECTS_DB_NAME)

        if os.path.exists(projects_db):

            conn = sqlite3.connect(projects_db)
            cursor = conn.cursor()
            cursor.execute(f'SELECT id, pid FROM {config.PROJECTS_TABLE}')

            terminated_projects = []

            for project_id, pid in cursor.fetchall():
                if not psutil.pid_exists(pid):
                    terminated_projects.append(project_id)

            seq = ','.join(['?'] * len(terminated_projects))
            cursor.execute(
                f'UPDATE {config.PROJECTS_TABLE} SET pid = -1 WHERE id in ({seq})',
                terminated_projects
            )
            conn.commit()
            conn.close()

    except BadSQLiteTableSchema as e:  # pylint: disable=invalid-name
        config.DB_SCHEMA['status'] = 'fail'
        config.DB_SCHEMA['message'] = str(e)


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

    if config.DB_SCHEMA['status'] == 'fail':
        return JSONResponse(config.DB_SCHEMA, HTTPStatus.INTERNAL_SERVER_ERROR)

    try:
        response = await call_next(request)

    except (BadProjectNameError, ProjectAlreadyExistsError) as e:
        return build_error_response(HTTPStatus.BAD_REQUEST, e)

    except (ProjectNotFoundError, RegisteredModelNotFoundError) as e:
        return build_error_response(HTTPStatus.NOT_FOUND, e)

    except ProjectIsAlreadyRunningError as e:
        return build_error_response(HTTPStatus.CONFLICT, e)

    except Exception as e:
        return build_error_response(HTTPStatus.INTERNAL_SERVER_ERROR, e)

    ip = request.headers.get('X-Forwarded-For', request.client.host)
    host = request.client.host.split(':', 1)[0]
    query_params = dict(request.query_params)

    # ISSUE: it's problematic to get body in middleware, links:
    # https://github.com/encode/starlette/issues/495,
    # https://github.com/tiangolo/fastapi/issues/394
    # body = dict(await request.body())

    log_params = [
        ('method', request.method),
        ('path', request.url.path),
        ('status', response.status_code),
        ('ip', ip),
        ('host', host),
        ('params', query_params)
        # ('body', body)
    ]

    line = json.dumps(dict(log_params))
    config.logger.info(line)
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

    final_response.headers['Access-Control-Allow-Origin'] = '*'
    final_response.status_code = response.status_code

    return final_response
