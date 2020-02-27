"""This module provides auxiliary functions"""

# pylint: disable=wrong-import-order

import socket


def get_free_tcp_port() -> int:
    """Get free tcp port in system
    Returns:
        int: port number
    """

    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind(('', 0))
    _, port = tcp.getsockname()
    tcp.close()

    return port
