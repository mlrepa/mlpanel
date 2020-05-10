"""This module provides auxiliary functions"""

# pylint: disable=wrong-import-order

from google.cloud import storage
import os
import socket
from typing import Text

from deploy.src.config import Config


conf = Config()


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


def upload_blob_to_gs(bucket_name: Text, source_file_name: Text,
                      destination_blob_name: Text) -> None:
    """
    Upload file to Google Cloud Storage.
    Args:
        bucket_name {Text}: bucket name
        source_file_name {Text}: name of file to upload
        destination_blob_name {Text}: blob name in the storage
    """

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)


def local_model_uri_to_gs_blob(model_uri: Text) -> Text:
    """
    Get gs blob name for local model.
    Args:
        model_uri {Text}: model uri
    Returns:
        Text: model blob name
    """

    return os.path.join(
        'mlpanel/cache/models', model_uri.replace(conf.get('WORKSPACE'), '').strip('/')
    )


def upload_local_mlflow_model_to_gs(model_uri: Text) -> None:
    """
    Upload local mlflow model to Google Cloud Storage.
    Args:
        model_uri {Text}: model uri
    """

    bucket_name = conf.get('bucket')
    model_blob = local_model_uri_to_gs_blob(model_uri)

    for file in os.listdir(model_uri):

        source_file_name = os.path.join(model_uri, file)
        destination_blob_name = os.path.join(model_blob, file)
        upload_blob_to_gs(bucket_name, source_file_name, destination_blob_name)
