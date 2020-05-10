"""This module provide auxiliary functions for this service"""

# pylint: disable=wrong-import-order

from http import HTTPStatus
import requests
from typing import Text, List, Dict

from projects.src.project_management import ProjectManager, ProjectNotFoundError


class RegisteredModelNotFoundError(Exception):
    """Registered model not found"""


def get_model_versions(project_id: int) -> List[Dict]:
    """Get all model versions by tracking server uri
    Args:
        project_id {int}: project id
    Returns:
        List[Dict]: list of model versions
    """

    project_manager = ProjectManager()
    tracking_uri = project_manager.get_internal_tracking_uri(project_id)
    model_versions_resp = requests.get(
        url=f'{tracking_uri}/api/2.0/preview/mlflow/model-versions/search'
    )
    model_versions = model_versions_resp.json().get('model_versions_detailed')

    return model_versions


def check_model_version_name(model_name: Text, model_version: Dict) -> bool:
    """Check model version name.
    Args:
        model_name {Text}: model name
        model_version {Dict}: model version dictionary
    Returns:
        True if model names are matches, otherwise false
    """

    model_version = model_version.get('model_version', {})
    registered_model = model_version.get('registered_model')

    return registered_model.get('name') == model_name


def filter_model_versions(
        model_versions: List[Dict],
        model_name: Text) -> List[Dict]:
    """Get model versions for specified model from input model versions list.
    Args:
        model_versions {List[Dict]}: input model versions list
        model_name {Text}: name of model
    Returns:
        List[Dict]: list of specified model versions
    """

    this_model_versions = list(filter(
        lambda model_version: check_model_version_name(model_name, model_version),
        model_versions
    ))

    return this_model_versions


def check_if_project_and_model_exist(project_id: int, model_id: Text) -> None:
    """Check if project and model are exist.
    Args:
        project_id {int}: project id
        model_id {Text}: model id (name)
    Raises:
        ProjectNotFoundError: if project does not exists;
        RegisteredModelNotFoundError: if project exists, but model does not exist
    """

    project_manager = ProjectManager()
    url = project_manager.get_internal_tracking_uri(project_id)

    if url is None:
        raise ProjectNotFoundError(f'Project with ID {project_id} not found')

    model_resp = requests.post(
        url=f'{url}/api/2.0/preview/mlflow/registered-models/get-details',
        json={'registered_model': {'name': model_id}}
    )

    if model_resp.status_code != HTTPStatus.OK:
        raise RegisteredModelNotFoundError(f'Model {model_id} not found')


def get_model_version_uri(project_id: int, model_id: Text, version: Text) -> Text:
    """Get model version URI.
    Args:
        project_id {int}: project id
        model_id {Text}: model id (name)
        version {Text}: model version
    Returns:
        Text: path to model package for model version
    """

    project_manager = ProjectManager()
    url = project_manager.get_internal_tracking_uri(project_id)
    model_resp = requests.post(
        url=f'{url}/api/2.0/preview/mlflow/registered-models/get-details',
        json={'registered_model': {'name': model_id}}
    )

    if model_resp.status_code != HTTPStatus.OK:

        if model_resp.status_code == HTTPStatus.NOT_FOUND:
            raise RegisteredModelNotFoundError(f'Model {model_id} not found')

        raise Exception(model_resp.text)

    this_model_versions = filter_model_versions(get_model_versions(project_id), model_id)

    for ver in this_model_versions:
        if ver.get('model_version', {}).get('version') == version:
            return ver.get('source')

    raise RegisteredModelNotFoundError(f'Version {version} of {model_id} not found')
