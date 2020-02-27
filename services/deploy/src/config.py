"""Global config module."""

# pylint: disable=global-statement

import os

GCP_CONFIG = None
WORKSPACE = os.getenv('WORKSPACE')
DEPLOY_DB_NAME = 'deploy.db'
DEPLOYMENTS_TABLE = 'deployment'


def create_workspace_dir() -> None:
    """Create workspace directory"""

    os.makedirs(WORKSPACE, exist_ok=True)


def check_environment_variable() -> None:
    """Check if all required environment variables are set.
    Raises:
        TypeError: if GCP_CONFIG is not dictionary
        EnvironmentError: if some required environment variable is not set
    """

    global GCP_CONFIG

    if WORKSPACE is None:
        raise EnvironmentError('Failed because WORKSPACE env var is not set')

    if not isinstance(GCP_CONFIG, dict):
        raise TypeError(f'GCP_CONFIG must be dictionary, not {type(GCP_CONFIG)}')

    for name, value in GCP_CONFIG.items():
        if value is None:
            raise EnvironmentError(f'Failed because {name} env var is not set')


def load_gcp_config_env_vars() -> None:
    """Load environment variables."""

    global GCP_CONFIG

    GCP_CONFIG = {
        'gcp_project': os.getenv('GCP_PROJECT'),
        'zone': os.getenv('GCP_ZONE'),
        'machine_type_name': os.getenv('GCP_MACHINE_TYPE'),
        'image': os.getenv('GCP_OS_IMAGE'),
        'bucket': os.getenv('GCP_BUCKET'),
        'docker_image': os.getenv('MODEL_DEPLOY_DOCKER_IMAGE'),
        'firewall': os.getenv('MODEL_DEPLOY_FIREWALL_RULE'),
        'port': os.getenv('MODEL_DEPLOY_DEFAULT_PORT'),
        'google_credentials_json': os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    }

    if GCP_CONFIG.get('google_credentials_json') is not None:
        check_environment_variable()
