"""Global config module."""

# pylint: disable=global-statement
# pylint: disable=invalid-name

import logging
import os
from logging.handlers import RotatingFileHandler
import time

from common.utils import validate_env_var


class Config:

    def __init__(self):

        self._load_env_vars()
        self._check_env_vars()

    def get(self, env_var):
        return self.env_vars.get(env_var)

    def get_logger(self, name):

        logger = logging.getLogger(name)
        worksapce = self.get('WORKSPACE')
        os.makedirs(worksapce, exist_ok=True)
        LOGFILE = os.path.join(worksapce, 'projects.log')
        LOGLEVEL = os.getenv('LOGLEVEL', 'INFO').upper()

        if LOGLEVEL not in logging._nameToLevel.keys():  # pylint: disable=protected-access
            LOGLEVEL = 'INFO'

        f_handler = RotatingFileHandler(LOGFILE, mode='a')
        f_handler.setLevel(LOGLEVEL)

        f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        f_format.converter = time.gmtime
        f_handler.setFormatter(f_format)

        logger.setLevel(LOGLEVEL)
        logger.addHandler(f_handler)

        return logger

    def _load_env_vars(self):

        self.env_vars = {
            'HOST_IP': os.getenv('HOST_IP', '0.0.0.0'),
            'WORKSPACE': os.getenv('WORKSPACE'),
            'ARTIFACT_STORE': os.getenv('ARTIFACT_STORE'),
            'TRACKING_SERVER_PORTS': os.getenv('TRACKING_SERVER_PORTS'),
            'TRACKING_SERVER_WORKERS': os.getenv('TRACKING_SERVER_WORKERS', 1),
            'PROJECTS_DB_NAME': os.getenv('PROJECTS_DB_NAME'),
            'DB_HOST': os.getenv('DB_HOST'),
            'DB_PORT': os.getenv('DB_PORT'),
            'DB_USER': os.getenv('POSTGRES_USER'),
            'DB_PASSWORD': os.getenv('POSTGRES_PASSWORD')
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

