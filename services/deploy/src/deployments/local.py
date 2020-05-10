"""This module provides functions for working with local deployments."""

import os
import subprocess as sp
from typing import Text, Tuple

from common.utils import kill
from deploy.src.config import Config
from deploy.src.utils import get_free_tcp_port


def create_local_deployment(model_uri: Text) -> Tuple[sp.Popen, int]:
    """Create local deployment process.
    Args:
        model_uri {Text}: path to model package
    Returns:
        Tuple[subprocess.Popen, int]: (process, deployment port)
    """

    conf = Config()
    port = get_free_tcp_port()
    log_path = os.path.join(conf.deployments_logs_dir, model_uri.replace('/','_') + '.log')
    process = sp.Popen(
        [
            f'mlflow models serve --no-conda -m '
            f'{model_uri} '
            f'--host 0.0.0.0 --port {port} --workers {conf.get("DEPLOY_SERVER_WORKERS")} '
            f'2>&1 | tee -a {log_path}'
        ],
        shell=True
    )

    return process, port


def stop_local_deployment(pid: int) -> None:
    """Stop local deployment.
    Args:
        pid {int}: process id
        proc {subprocess.Popen}: deployment process
    """

    kill(pid)
