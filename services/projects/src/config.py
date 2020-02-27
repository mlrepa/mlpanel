"""Global config module."""

# pylint: disable=global-statement
# pylint: disable=invalid-name

import logging
import os
import time
from logging.handlers import RotatingFileHandler

from projects.src.utils import get_external_ip


HOST_MODE = os.getenv('HOST_MODE', 'local')
HOST_IP = '0.0.0.0'

if HOST_MODE == 'remote':
    HOST_IP = get_external_ip()

WORKSPACE = os.getenv('WORKSPACE')

# Check if WORKSPACE is set
if WORKSPACE is None:
    raise EnvironmentError('Failed because env var WORKSPACE is not set')

PROJECTS_DB_NAME = 'projects.db'
PROJECTS_TABLE = 'project'

LAST_MLFLOW_UI_URL = None

DB_SCHEMA = {
    'status': 'ok',
    'message': ''
}

logger = logging.getLogger(__name__)


def create_workspace_dir() -> None:
    """Create workspace directory"""

    os.makedirs(WORKSPACE, exist_ok=True)


def set_logger() -> None:
    """Set logger"""

    create_workspace_dir()

    LOGFILE = os.path.join(WORKSPACE, 'server.log')
    LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()

    if LOGLEVEL not in logging._nameToLevel.keys():  # pylint: disable=protected-access
        LOGLEVEL = 'INFO'

    f_handler = RotatingFileHandler(LOGFILE, mode='a')
    f_handler.setLevel(LOGLEVEL)

    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    f_format.converter = time.gmtime
    f_handler.setFormatter(f_format)

    logger.setLevel(LOGLEVEL)
    logger.addHandler(f_handler)
