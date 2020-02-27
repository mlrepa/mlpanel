"""This module provides functions for working with local deployments."""

import subprocess as sp
from typing import Optional, Text, Tuple

from deploy.src.utils import get_free_tcp_port
from common.utils import kill


def create_local_deployment(model_uri: Text, host: Text) -> Tuple[sp.Popen, int]:
    """Create local deployment process.
    Args:
        model_uri {Text}: path to model package
        host {Text}: host address
    Returns:
        Tuple[subprocess.Popen, int]: (process, deployment port)
    """

    port = get_free_tcp_port()
    process = sp.Popen(
        [
            f'mlflow models serve --no-conda -m '
            f'{model_uri} '
            f'-h {host} -p {port}'
        ],
        shell=True
    )

    return process, port


def stop_local_deployment(pid: int, proc: Optional[sp.Popen]) -> None:
    """Stop local deployment.
    Args:
        pid {int}: process id
        proc {subprocess.Popen}: deployment process
    """

    kill(pid)

    # TODO (Alex): find how to avoid zombie processes without call method "communicate()"
    if isinstance(proc, sp.Popen) and proc.poll() is None:
        # Call method "communicate()" to really stop process (avoids zombie process)
        proc.communicate()
