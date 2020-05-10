"""This model provides common auxiliary functions for all services"""

import datetime
import os
from http import HTTPStatus
from typing import Text, Union

import psutil
from google.cloud import storage
from starlette.responses import JSONResponse


class ModelDoesNotExistError(Exception):
    """Model does not exists"""


class InvalidEnvVarValueError(Exception):
    """Invalid env var value"""


def get_rfc3339_time() -> Text:
    """Get timestamp in rfc3339 format

    Returns:
        Text -- timestamp

    """

    return datetime.datetime.utcnow().isoformat('T') + 'Z'


def error_response(http_response_code: Union[HTTPStatus, int], message: Text) -> JSONResponse:
    """Build error json response

    Args:
        http_response_code {int} -- http response status code
        message {Text} -- response message

    Returns:

        JSONResponse -- FastAPI json response

    """

    if isinstance(http_response_code, HTTPStatus):
        http_response_code = http_response_code.value

    return JSONResponse(dict(
        code=str(http_response_code),
        message=message
    ), http_response_code)


def build_error_response(status_code: HTTPStatus, e: Exception) -> JSONResponse:  # pylint: disable=invalid-name
    """Build error response.
    Args:
        status_code {HTTPStatus}: status code
        e {Exception}: exception object
    Returns:
        JSONResponse: FastAPI json response
    """

    error_resp = error_response(
        http_response_code=status_code,
        message=str(e)
    )

    return error_resp


def is_model(folder: Text) -> bool:
    """Check if the folder is MLflow model.
    Folder is MLflow model then and only then if it contains file MLmodel.
    Args:
        folder {Text}: folder path
    Returns:
        bool: True if folder is MLflow model, otherwise False
    """

    model_identifier_filename = 'MLmodel'

    if folder.startswith('gs://'):

        bucket, *model_folder_path_parts = folder.strip('gs://').split('/')
        model_folder_path = '/'.join(model_folder_path_parts)
        client = storage.Client()
        bucket = client.get_bucket(bucket)
        model_blob = bucket.blob(os.path.join(model_folder_path, model_identifier_filename))

        return model_blob.exists()

    if os.path.exists(folder) and os.path.isdir(folder):
        return model_identifier_filename in os.listdir(folder)

    return False


def kill(proc_pid: int) -> None:
    """Kill process with child processes
    Arguments:
        proc_pid {int} -- process id
    """

    if not psutil.pid_exists(proc_pid):
        return

    process = psutil.Process(proc_pid)

    for proc in process.children(recursive=True):
        proc.kill()

    process.kill()


def is_remote(path: Text) -> bool:
    """Check if the path is in remote storage.
    Args:
        path {Text}: path of file or folder
    Returns:
        bool: True if path is in remote storage, otherwise False
    """

    # TODO(Alex): add check for another remote storages (s3, ...) when they will be supported
    if path.startswith('gs://'):
        return True

    return False


def validate_env_var(name: Text, value: Text) -> None:

    if ' ' in value:
        raise InvalidEnvVarValueError(f'Invalid value "{value}" of env var {name}')


def get_utc_timestamp() -> Text:
    """Get utc timestamp.
    Returns:
        Text: utc timestamp
    """

    return str(datetime.datetime.utcnow().timestamp() * 1000)