"""This module provides functions for working with GCP deployments."""

import time
from typing import Dict, Text


from deploy.src.deployments.gcp_deploy_utils import gcp_deploy_model, gcp_get_external_ip, \
    gcp_delete_instance


def create_gcp_deployment(model_uri: Text, conf: Dict, instance_name: Text) -> None:
    """Create gcp deployment.
    Args:
        model_uri {Text}: path to model package
        conf {Dict}: GCP deployment config
        instance_name {Text}: GCE instance name
    """

    gcp_deploy_model(
        model_uri=model_uri,
        instance_name=instance_name,
        **conf
    )


def stop_gcp_deployment(instance_name: Text, conf: Dict) -> None:
    """Stop GCP deployment
    Args:
        instance_name {Text}: GCE instance name
        conf {Dict}: GCP deployment config
    """

    gcp_delete_instance(
        gcp_project=conf.get('gcp_project'),
        instance=instance_name,
        zone=conf.get('zone')
    )


def wait_gcp_host_ip(instance_name: Text, conf: Dict, timeout: int) -> Text:
    """Wait GCE instance ip address
    Args:
        instance_name {Text}: GCE instance name
        conf {Dict}: GCP deployment config
        timeout {int}: waiting timeout in seconds
    Returns:
        Text: external ip address of instance
    """

    start_wait_host = time.time()
    host = None

    while host is None:

        host = gcp_get_external_ip(
            gcp_project=conf.get('gcp_project'),
            instance=instance_name,
            zone=conf.get('zone')
        )
        time_passed = time.time() - start_wait_host

        if time_passed > timeout:
            break

    return host
