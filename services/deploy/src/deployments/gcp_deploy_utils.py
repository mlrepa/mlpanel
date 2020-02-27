"""
    Module provides functions for working with GCE instances: create, check running,
get external ip, delete instances; working with firewall rules.
"""

# pylint: disable=wrong-import-order
import time

import googleapiclient.discovery
import googleapiclient.errors
from typing import Dict, List, Optional, Text


def gcp_create_instance(name: Text, gcp_project: Text, zone: Text, machine_type_name: Text,
                        image: Text, bucket: Text, startup_script: Text) -> Dict:
    """Create Google Compute Engine instance.
    Args:
        name {Text}: instance name
        gcp_project {Text}: gcp project id
        zone {Text}: zone
        machine_type_name {Text}: machine type
        image {Text}: image name
        bucket {Text}: bucket name
        startup_script {Text}: content of startup script
    Returns:
        Dict: create operation dictionary:
                {
                    'id': '<operation_id>',
                    'name': '<operation_name>',
                    'zone': ': <BASE_PATH>/zones/<zone>',
                    'operationType': 'insert',
                    'targetLink': ': <BASE_PATH>/zones/<zone>/instances/<instance>',
                    'targetId': '<target_id>',
                    'status': 'RUNNING',
                    'user': '<google_user_id>-compute@developer.gserviceaccount.com',
                    'progress': 0,
                    'insertTime': '2019-12-06T04:08:57.663-08:00',
                    'startTime': '2019-12-06T04:08:57.666-08:00',
                    'selfLink': ': <BASE_PATH>/zones/<zone>/operations/<operation_id>',
                    'kind': 'compute#operation'
                }
                where <BASE_PATH>=https://www.googleapis.com/compute/v1/gcp_projects/<gcp_project>
    """
    # pylint: disable=too-many-arguments

    compute = googleapiclient.discovery.build('compute', 'v1')
    image_response = compute.images().get(image=image, project=gcp_project).execute()  # pylint: disable=no-member
    source_disk_image = image_response['selfLink']
    machine_type = f'zones/{zone}/machineTypes/{machine_type_name}'
    config = {
        'name': name,
        'machineType': machine_type,
        # Specify the boot disk and the image to use as a source.
        'disks': [
            {
                'boot': True,
                'autoDelete': True,
                'initializeParams': {
                    'sourceImage': source_disk_image,
                }
            }
        ],
        # Specify a network interface with NAT to access the public Internet.
        'networkInterfaces': [{
            'network': 'global/networks/default',
            'accessConfigs': [
                {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
            ]
        }],
        # Allow the instance to access cloud storage and logging.
        'serviceAccounts': [{
            'email': 'default',
            'scopes': [
                'https://www.googleapis.com/auth/devstorage.read_write',
                'https://www.googleapis.com/auth/logging.write'
            ]
        }],
        # Metadata is readable from the instance and allows you to
        # pass configuration from deployment scripts to instances.
        'metadata': {
            'items': [
                {
                    # Startup script is automatically executed by the instance upon startup.
                    'key': 'startup-script',
                    'value': startup_script
                },
                {
                    'key': 'bucket',
                    'value': bucket
                }
            ]
        }
    }

    return compute.instances().insert(  # pylint: disable=no-member
        project=gcp_project,
        zone=zone,
        body=config).execute()


def gcp_instance_healthcheck(gcp_project: Text, instance: Text, zone: Text) -> bool:
    """Check if instance is running
    Args:
        gcp_project {Text}: gcp project id
        instance {Text}: instance name
        zone {Text}: zone
    Returns:
        bool: True if instance is running, otherwise False
    """

    compute = googleapiclient.discovery.build('compute', 'v1')
    instances = compute.instances()  # pylint: disable=no-member
    try:
        inst = instances.get(project=gcp_project, instance=instance, zone=zone).execute()
    except googleapiclient.errors.HttpError:
        return False

    return inst.get('status') == 'RUNNING'


def gcp_get_external_ip(gcp_project: Text, instance: Text, zone: Text) -> Optional[Text]:
    """Get instance external ip
        Args:
            gcp_project {Text}: gcp project id
            instance {Text}: instance name
            zone {Text}: zone
        Returns:
            Text: external ip
        """

    if not gcp_instance_healthcheck(gcp_project, instance, zone):
        return None

    compute = googleapiclient.discovery.build('compute', 'v1')
    instances = compute.instances()  # pylint: disable=no-member
    inst = instances.get(project=gcp_project, instance=instance, zone=zone).execute()
    network_interfaces = inst.get('networkInterfaces', [])

    if len(network_interfaces) == 0:
        return None

    access_configs = network_interfaces[0].get('accessConfigs', [])

    if len(access_configs) == 0:
        return None

    return access_configs[0].get('natIP')


def gcp_delete_instance(gcp_project: Text, instance: Text, zone: Text) -> Dict:
    """Delete instance
    Args:
        gcp_project {Text}: gcp project id
        instance {Text}: instance name
        zone {Text}: zone
    Returns:
        Dict: instance delete operation dictionary:

            {
                 'id': '<operation_id>',
                 'name': '<operation_name>',
                 'zone': ': <BASE_PATH>/zones/<zone>',
                 'operationType': 'delete',
                 'targetLink': ': <BASE_PATH>/zones/<zone>/instances/<instance>',
                 'targetId': '<target_id>',
                 'status': 'RUNNING',
                 'user': '<google_user_id>-compute@developer.gserviceaccount.com',
                 'progress': 0,
                 'insertTime': '2019-12-06T07:17:32.880-08:00',
                 'startTime': '2019-12-06T07:17:32.897-08:00',
                 'selfLink': ': <BASE_PATH>/zones/<zone>/operations/<operation_name>',
                 'kind': 'compute#operation'
            }
            where <BASE_PATH>=https://www.googleapis.com/compute/v1/gcp_projects/<gcp_project>
    """

    compute = googleapiclient.discovery.build('compute', 'v1')
    instances = compute.instances()  # pylint: disable=no-member
    operation = instances.delete(project=gcp_project, instance=instance, zone=zone)

    return operation.execute()


def gcp_firewall_exists(gcp_project: Text, firewall: Text) -> bool:
    """
    Args:
        gcp_project {Text}: gcp project id
        firewall {Text}: firewall rule name
    Returns:
        bool: True if firewall rule exists, otherwise False
    """

    compute = googleapiclient.discovery.build('compute', 'v1')
    firewalls = compute.firewalls()  # pylint: disable=no-member
    rules = firewalls.list(project=gcp_project).execute()

    for rule in rules.get('items', []):
        if rule.get('name') == firewall:
            return True

    return False


def gcp_create_firewall(gcp_project: Text, name: Text, description: Text = '',
                        network: Text = 'global/networks/default', priority: int = 1000,
                        source_ranges: List[Text] = None, allowed: List[Dict] = None,
                        direction: Text = 'INGRESS', log_config_enable: bool = False) -> Dict:
    """Create new firewall rule
    Args:
        gcp_project {Text}: gcp project id
        name {Text}: firewall rule name
        description {Text}: description
        network {Text}: network name
        priority {int}: rule priority
        sourceRanges {List[Text]}: IPs range
        allowed {List[Dict]}: protocols and ports setting
        direction {Text}: INGRESS or EGRESS
        log_config_enable {Text}: if logging is enabled, logs will be exported to Stackdriver
    Returns:
        Dict: firewall create operation dictionary:
            {
                'id': '<operation_id>',
                'name': '<operation_name>',
                'operationType': 'insert',
                'targetLink': ': <BASE_PATH>/global/firewalls/<firewall_rule_name>',
                'targetId': '<target_id>',
                'status': 'RUNNING',
                'user': '<google_user_id>-compute@developer.gserviceaccount.com',
                'progress': 0,
                'insertTime': '2019-12-06T05:33:06.123-08:00',
                'startTime': '2019-12-06T05:33:06.176-08:00',
                'selfLink': ': <BASE_PATH>/global/operations/<operation_name>',
                'kind': 'compute#operation'
            }
            where <BASE_PATH>=https://www.googleapis.com/compute/v1/gcp_projects/<gcp_project>
    """
    # pylint: disable=too-many-arguments

    if source_ranges is None:
        source_ranges = ['0.0.0.0/0']

    if allowed is None:
        allowed = [{'IPProtocol': 'tcp', 'ports': ['8080']}]

    log_config = {'enable': log_config_enable}
    body = {
        'name': name,
        'description': description,
        'network': network,
        'priority': priority,
        'sourceRanges': source_ranges,
        'allowed': allowed,
        'direction': direction,
        'logConfig': log_config
    }
    compute = googleapiclient.discovery.build('compute', 'v1')
    firewalls = compute.firewalls()  # pylint: disable=no-member
    operation = firewalls.insert(
        project=gcp_project,
        body=body
    )

    return operation.execute()


def gcp_add_ports(gcp_project: Text, firewall: Text, ports: List[Text], protocol: Text = 'tcp'):
    """Add ports or ports range to existed firewall
    Args:
        gcp_project {Text}: gcp project id
        firewall {Text}: firewall rule name
        ports {List[Text]}: list of ports or port ranges
        protocol {Text}: protocol type
    Returns:
        Dict: firewall update operation dictionary:

            {
                 'id': '<operation_id>',
                 'name': '<operation_name>',
                 'operationType': 'update',
                 'targetLink': ': <BASE_PATH>/global/firewalls/<firewall_rule_name>',
                 'targetId': '<target_id>',
                 'status': 'RUNNING',
                 'user': '<google_user_id>-compute@developer.gserviceaccount.com',
                 'progress': 0,
                 'insertTime': '2019-12-06T06:35:38.844-08:00',
                 'startTime': '2019-12-06T06:35:38.853-08:00',
                 'selfLink': ': <BASE_PATH>/global/operations/<operation_name>',
                 'kind': 'compute#operation'
            }
            where <BASE_PATH>=https://www.googleapis.com/compute/v1/gcp_projects/<gcp_project>
    """

    compute = googleapiclient.discovery.build('compute', 'v1')
    firewalls = compute.firewalls()  # pylint: disable=no-member
    rule = firewalls.get(project=gcp_project, firewall=firewall).execute()
    allowed = rule.get('allowed', [])

    for item in allowed:
        if item.get('IPProtocol') == protocol:
            item['ports'] = list(
                set(item.get('ports', [])).union(ports)
            )

    operation = firewalls.update(
        project=gcp_project,
        firewall=firewall,
        body={
            'allowed': allowed
        }
    )

    return operation.execute()


def gcp_deploy_model(model_uri: Text, docker_image: Text, instance_name: Text,
                     gcp_project: Text, zone: Text, machine_type_name: Text, image: Text,
                     bucket: Text, firewall: Text, port: Text, google_credentials_json: Text
                     ) -> None:
    """Deploy model
     Args:
        model_uri {Text}: model URI
        docker_image {Text}: docker image
        instance_name {Text}: instance name
        gcp_project {Text}: gcp project id
        zone {Text}: zone
        machine_type_name {Text}: machine type
        image {Text}: image name
        bucket {Text}: bucket name
        startup_script {Text}: content of startup script,
        firewall {Text}: firewall rule name
        port {Text}: model port
        google_credentials_json {Text}: path to Google credentials json
    """
    # pylint: disable=too-many-arguments

    google_credentials = open(google_credentials_json).read()
    google_credentials = ''.join(google_credentials.split('\n'))
    # pylint: disable=line-too-long
    startup_script = f'!/bin/bash\n\n' \
                     f'echo \'{google_credentials}\' >> /home/gac.json &&  ' \
                     f'docker run -v /home/gac.json:/root/gac.json -p {port}:{port} {docker_image} ' \
                     f'/bin/bash -c ' \
                     f'"export GOOGLE_APPLICATION_CREDENTIALS=/root/gac.json && ' \
                     f'mlflow models serve --no-conda -m {model_uri} -h 0.0.0.0 -p {port}" '
    gcp_create_instance(
        name=instance_name,
        gcp_project=gcp_project,
        zone=zone,
        machine_type_name=machine_type_name,
        image=image,
        bucket=bucket,
        startup_script=startup_script
    )

    if not gcp_firewall_exists(gcp_project=gcp_project, firewall=firewall):
        gcp_create_firewall(
            gcp_project=gcp_project,
            name=firewall,
            allowed=[{'IPProtocol': 'tcp', 'ports': [port]}]
        )
    else:
        gcp_add_ports(
            gcp_project=gcp_project,
            firewall=firewall,
            ports=[port]
        )


def generate_gcp_instance_name() -> Text:
    """Generate instance name
    Returns:
        Text: instance name containing argument
    """

    return f'deployment-{time.time_ns()}'