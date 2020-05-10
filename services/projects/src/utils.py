"""This module provides auxiliary functions"""

# pylint: disable=wrong-import-order

import json
import psutil
from starlette.requests import Request
from typing import Dict

from projects.src.config import Config


conf = Config()
logger = conf.get_logger(__name__)


def bytes2mb(byte_number: int) -> int:
    """Converts bytes to megabytes.
    Args:
        byte_number {int}: number of bytes
    Returns:
        int: megabytes
    """

    return byte_number / (1024 ** 2)


def system_stat() -> Dict:
    """Get system resource statistics.
    Returns:
        Dict: example:
                {
                    'cpu': {
                        'usage': 41.3,
                        'units': 'percentage'
                    },
                    'memory': {
                        'usage': {
                            'total': 11700.4296875,
                            'available': 4668.93359375,
                            'used': 5799.63671875,
                            'free': 1539.7890625,
                            'active': 7013.98828125,
                            'inactive': 2424.76171875,
                            'buffers': 1784.5,
                            'cached': 2576.50390625,
                            'shared': 928.76171875,
                            'slab': 478.15625
                        },
                        'units': 'mb',
                        'percentage': 60.1
                     }
                }
    """

    return {
        'cpu': {
            'usage': psutil.cpu_percent(),
            'units': 'percentage'
        },
        'memory': {
            'usage': {
                k: bytes2mb(v)
                for k, v in psutil.virtual_memory()._asdict().items()
                if k != 'percent'
            },
            'units': 'mb',
            'percentage': psutil.virtual_memory().percent
        }
    }


def process_stat(pid: int) -> Dict:
    """Get statistics for process.
    Args:
        proc_id {int}: process id
    Returns:
        Dict: example:
                {
                    'cpu': {
                        'usage': 0.0,
                        'units': 'percentage'
                    },
                    'memory': {
                        'usage': {
                            'rss': 193.27734375,
                            'vms': 876.59765625,
                            'shared': 100.484375,
                            'text': 130.71484375,
                            'lib': 0.0,
                            'data': 273.8828125,
                            'dirty': 0.0,
                            'uss': 103.1875,
                            'pss': 108.6533203125,
                            'swap': 0.0
                        },
                        'units': 'mb',
                        'percentage': 1.6518824428857115
                    }
                }
    """

    process = psutil.Process(pid=pid)

    return {
        'cpu': {
            'usage': process.cpu_percent(),
            'units': 'percentage'
        },
        'memory': {
            'usage': {k: bytes2mb(v) for k, v in process.memory_full_info()._asdict().items()},
            'units': 'mb',
            'percentage': process.memory_percent()
        }
    }


def log_request(request: Request, body_params: Dict = None):

    ip = request.headers.get('X-Forwarded-For', request.client.host)
    host = request.client.host.split(':', 1)[0]
    query_params = dict(request.query_params)

    log_params = [
        ('method', request.method),
        ('path', request.url.path),
        ('ip', ip),
        ('host', host),
        ('params', query_params),
        ('body', body_params or {})
    ]

    line = json.dumps(dict(log_params))
    logger.debug(line)