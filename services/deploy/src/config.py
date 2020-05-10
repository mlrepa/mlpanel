"""Global config module."""

# pylint: disable=global-statement

import os

from common.utils import validate_env_var


class Config:

    def __init__(self):

        self._load_env_vars()
        self._check_env_vars()

        self.deployments_logs_dir = os.path.join(self.get('WORKSPACE'), 'deployments_logs')
        os.makedirs(self.get('WORKSPACE'), exist_ok=True)
        os.makedirs(self.deployments_logs_dir, exist_ok=True)

    def get(self, env_var):
        return self.env_vars.get(env_var)

    def get_gcp_config(self):

        gcp_config = {
            'gcp_project': self.env_vars.get('GCP_PROJECT'),
            'zone': self.env_vars.get('GCP_ZONE'),
            'machine_type_name': self.env_vars.get('GCP_MACHINE_TYPE'),
            'image': self.env_vars.get('GCP_OS_IMAGE'),
            'bucket': self.env_vars.get('GCP_BUCKET'),
            'docker_image': self.env_vars.get('MODEL_DEPLOY_DOCKER_IMAGE'),
            'firewall': self.env_vars.get('MODEL_DEPLOY_FIREWALL_RULE'),
            'port': self.env_vars.get('MODEL_DEPLOY_DEFAULT_PORT'),
            'google_credentials_json': self.env_vars.get('GOOGLE_APPLICATION_CREDENTIALS')
        }

        return gcp_config

    def _load_env_vars(self):

        self.env_vars = {
            'WORKSPACE': os.getenv('WORKSPACE'),
            'DEPLOY_DB_NAME': os.getenv('DEPLOY_DB_NAME'),
            'DB_HOST': os.getenv('DB_HOST'),
            'DB_PORT': os.getenv('DB_PORT'),
            'DB_USER': os.getenv('POSTGRES_USER'),
            'DEPLOY_SERVER_WORKERS': os.getenv('DEPLOY_SERVER_WORKERS', 1),
            'DB_PASSWORD': os.getenv('POSTGRES_PASSWORD'),
            'GCP_PROJECT': os.getenv('GCP_PROJECT', ''),
            'GCP_ZONE': os.getenv('GCP_ZONE', ''),
            'GCP_MACHINE_TYPE': os.getenv('GCP_MACHINE_TYPE', ''),
            'GCP_OS_IMAGE': os.getenv('GCP_OS_IMAGE', ''),
            'GCP_BUCKET': os.getenv('GCP_BUCKET', ''),
            'MODEL_DEPLOY_DOCKER_IMAGE': os.getenv('MODEL_DEPLOY_DOCKER_IMAGE', ''),
            'MODEL_DEPLOY_FIREWALL_RULE': os.getenv('MODEL_DEPLOY_FIREWALL_RULE', ''),
            'MODEL_DEPLOY_DEFAULT_PORT': os.getenv('MODEL_DEPLOY_DEFAULT_PORT', ''),
            'GOOGLE_APPLICATION_CREDENTIALS': os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')
        }

    def _check_env_vars(self):
        """Check if all required environment variables are set.
            Raises:
                EnvironmentError: if some required environment variable is not set
                InvalidEnvVarValueError: if some environment variable is invalid
            """

        for name, value in self.env_vars.items():

            if value is None:
                raise EnvironmentError(f'Failed because {name} env var is not set')

            validate_env_var(name, str(value))

