"""
This module contains class for deployments management - DeployManager.
It allows to create, run, stop and delete deployments of different types.

Deployment is process which loads model and is available by http.
Models are deployed via MLflow. Deployment has two endpoints:
    * /ping = healthcheck;
    * /invocations = predict.
More information about MLflow models deploy:
    https://www.mlflow.org/docs/latest/models.html#deploy-mlflow-models

Now it's supported types of deployments:
    * local - runs new process locally;
    * gcp - creates new GCE instance and runs MLflow model deploy process on it.
"""

# pylint: disable=wrong-import-order

import os
import requests
import sqlite3
from typing import Dict, List, Text

from common.types import StrEnum
from common.utils import get_rfc3339_time, is_remote
from deploy.src import config
from deploy.src.deployments.gcp import create_gcp_deployment, stop_gcp_deployment, wait_gcp_host_ip
from deploy.src.deployments.gcp_deploy_utils import gcp_get_external_ip, generate_gcp_instance_name
from deploy.src.deployments.local import create_local_deployment, stop_local_deployment
from deploy.src.deployments.utils import mlflow_model_predict


class DeploymentNotFoundError(Exception):
    """Deployment not found"""


class InvalidDeploymentType(Exception):
    """Invalid deployment type"""


class LocalModelDeployRemotelyError(Exception):
    """Local model cannot be deployed remotely"""


class DeploymentStatus(StrEnum):
    """Deployment status enum.
    Statuses:
        * NOT_FOUND - there is no record in database;
        * RUNNING - deployment process is running;
        * STOPPED - deployment process is stopped;
        * DELETED - deployment is marked as deleted in database.
    """

    NOT_FOUND = 'not found'
    RUNNING = 'running'
    STOPPED = 'stopped'
    DELETED = 'deleted'


class DeploymentType(StrEnum):
    """Deployment type"""

    LOCAL = 'local'
    GCP = 'gcp'


class DeployManager:
    """
    Manage deployments.
    Methods:
        create(Deployment): creates new deployment.
        get_status(Deployment): get deployment status.
        predict(Deployment, str): predict data on deployment.
        stop(Deployment): stop deployment.
        list(): get deployments list.
    """
    #  pylint: disable=too-many-instance-attributes
    def __init__(self):
        """
        Args:
            workspace {Text}: workspace folder
            gcp_config {Dict}: config for GCP deployment
        """
        # pylint: disable=invalid-name

        self._WORKSPACE = config.WORKSPACE
        self._GCP_CONFIG = config.GCP_CONFIG
        self._LOCAL_DEPLOYMENT_HOST = '0.0.0.0'
        self._GCP_INSTANCE_CONNECTION_TIMEOUT = 30
        self._DEPLOY_DB_NAME = config.DEPLOY_DB_NAME
        self._DEPLOY_DB = os.path.join(self._WORKSPACE, self._DEPLOY_DB_NAME)
        self._DEPLOYMENTS_TABLE = config.DEPLOYMENTS_TABLE
        self._deploy_table_schema = {
            'id': 'INTEGER UNIQUE',
            'project_id': 'INTEGER',
            'model_id': 'TEXT',
            'version': 'TEXT',
            'model_uri': 'TEXT',
            'host': 'TEXT',
            'port': 'INTEGER',
            'pid': 'INTEGER',
            'instance_name': 'TEXT',
            'type': 'TEXT',
            'created_at': 'TIMESTAMP',
            'last_updated_at': 'TIMESTAMP',
            'status': 'TEXT'
        }
        self._connect_db()
        self._local_deployments_processes = {}

    def create_deployment(self, project_id: int, model_id: Text, model_version: Text,
                          model_uri: Text, deployment_type: Text) -> int:
        """Create deployment.
        Args:
            project_id {int}: project id
            model_id {Text}: model id (name)
            model_version {Text}: model version
            model_uri {Text}: path to model package
            deployment_type {Text}: deployment type
        Returns:
            int: id of created deployment
        """
        # pylint: disable=too-many-arguments

        instance_name = ''
        pid = -1

        if deployment_type == DeploymentType.LOCAL:

            host = self._LOCAL_DEPLOYMENT_HOST
            process, port = create_local_deployment(model_uri, self._LOCAL_DEPLOYMENT_HOST)
            pid = process.pid
            self._local_deployments_processes[pid] = process

        elif deployment_type == DeploymentType.GCP:

            if not is_remote(model_uri):
                raise LocalModelDeployRemotelyError(
                    f'Model {model_uri} is local, it cannot be deployed remotely')

            instance_name = generate_gcp_instance_name()
            create_gcp_deployment(model_uri, self._GCP_CONFIG, instance_name)
            port = self._GCP_CONFIG.get('port')
            host = wait_gcp_host_ip(
                instance_name, self._GCP_CONFIG, self._GCP_INSTANCE_CONNECTION_TIMEOUT)

        else:
            raise InvalidDeploymentType(f'Invalid deployment type: {deployment_type}')

        deployment_id = self._insert_new_deployment_in_db(
            project_id, model_id, model_version, model_uri,
            host, port, pid, instance_name, deployment_type
        )

        return deployment_id

    def run(self, deployment_id: int) -> None:
        """Run deployment.
        Args:
            deployment_id {int}: deployment id
        """

        self._cursor.execute(
            f'SELECT type, model_uri, instance_name, status '
            f'FROM {self._DEPLOYMENTS_TABLE} '
            f'WHERE id = {deployment_id}'
        )
        deployment = self._cursor.fetchone()

        if deployment is None:
            raise DeploymentNotFoundError(f'Deployment with ID {deployment_id} not found')

        deployment_type, model_uri, instance_name, status = deployment

        if status == DeploymentStatus.RUNNING:
            return

        if deployment_type == DeploymentType.LOCAL:

            host = self._LOCAL_DEPLOYMENT_HOST
            process, port = create_local_deployment(model_uri, self._LOCAL_DEPLOYMENT_HOST)
            pid = process.pid
            self._local_deployments_processes[pid] = process

        elif deployment_type == DeploymentType.GCP:

            pid = -1
            port = self._GCP_CONFIG.get('port')
            create_gcp_deployment(model_uri, self._GCP_CONFIG, instance_name)
            host = wait_gcp_host_ip(
                instance_name, self._GCP_CONFIG, self._GCP_INSTANCE_CONNECTION_TIMEOUT)

        else:
            raise InvalidDeploymentType(f'Invalid deployment type: {deployment_type}')

        self._cursor.execute(
            f'UPDATE {self._DEPLOYMENTS_TABLE} '
            f'SET host = ?, port = ?, status = ?, pid = ?, last_updated_at = ? '
            f'WHERE id = {deployment_id}',
            (host, port, str(DeploymentStatus.RUNNING), pid, get_rfc3339_time())
        )
        self._conn.commit()

    def stop(self, deployment_id: int) -> None:
        """Stop deployment.
        Args:
            deployment_id {int}: deployment id
        """

        self._cursor.execute(
            f'SELECT status, type, pid, instance_name '
            f'FROM {self._DEPLOYMENTS_TABLE} '
            f'WHERE id = {deployment_id} AND '
            f'      status <> "{str(DeploymentStatus.DELETED)}"'
        )
        deployment = self._cursor.fetchone()

        if deployment is None:
            raise DeploymentNotFoundError(f'Deployment with ID {deployment_id} not found')

        status, deployment_type, pid, instance_name = deployment

        if status == DeploymentStatus.STOPPED:
            return

        if deployment_type == DeploymentType.LOCAL:
            proc = self._local_deployments_processes.get(pid)
            stop_local_deployment(pid, proc)

        elif deployment_type == DeploymentType.GCP:
            stop_gcp_deployment(instance_name, self._GCP_CONFIG)

        else:
            raise InvalidDeploymentType(f'Invalid deployment type: {deployment_type}')

        self._cursor.execute(
            f'UPDATE {self._DEPLOYMENTS_TABLE} '
            f'SET status = ?, host = ?, port = ?, last_updated_at = ? '
            f'WHERE id = {deployment_id}',
            (str(DeploymentStatus.STOPPED), None, None, get_rfc3339_time())
        )
        self._conn.commit()

    def predict(self, deployment_id: int, data: Text) -> requests.Response:
        """Predict data on deployment.
        Args:
            deployment_id {int}: deployment id
            data {Text}: data to predict
        """

        self._cursor.execute(
            f'SELECT host, port '
            f'FROM {self._DEPLOYMENTS_TABLE} '
            f'WHERE id = {deployment_id} AND '
            f'      status <> "{str(DeploymentStatus.DELETED)}"'
        )
        host_port = self._cursor.fetchone()

        if host_port is None:
            raise DeploymentNotFoundError(f'Deployment with ID {deployment_id} not found')

        host, port = host_port
        response = mlflow_model_predict(host, port, data)

        return response

    def delete(self, deployment_id: int) -> None:
        """Delete deployment (mark as deleted.
        Args:
            deployment_id {int}: deployment id
        """

        self.stop(deployment_id)
        self._cursor.execute(
            f'UPDATE {self._DEPLOYMENTS_TABLE} '
            f'SET status = ?, host = ?, port = ?, last_updated_at = ? '
            f'WHERE id = {deployment_id}',
            (str(DeploymentStatus.DELETED), None, None, get_rfc3339_time())
        )
        self._conn.commit()

    def list(self) -> List[Dict]:
        """Get list of deployments info.
        Returns:
            List[Dict]
        """

        self._cursor.execute(
            f'SELECT id, project_id, model_id, version, model_uri, '
            f'type, created_at, instance_name, status, host, port '
            f'FROM {self._DEPLOYMENTS_TABLE} '
            f'WHERE status <> "{str(DeploymentStatus.DELETED)}"'
        )
        rows = self._cursor.fetchall()
        deployments = []

        for row in rows:
            deployments.append({
                'id': str(row[0]),
                'project_id': str(row[1]),
                'model_id': row[2],
                'version': row[3],
                'model_uri': row[4],
                'type': row[5],
                'created_at': row[6],
                'status': row[8],
                'host': row[9],
                'port': str(row[10]) if row[10] is not None else row[10]
            })

        return deployments

    def ping(self, deployment_id: int) -> bool:
        """Ping deployment.
        Args:
            deployment_id {int}: deployment id
        Returns:
            True deployment is available by http, otherwise False
        """

        self._cursor.execute(
            f'SELECT host, port, status '
            f'FROM {self._DEPLOYMENTS_TABLE} '
            f'WHERE id = "{deployment_id}"'
        )
        deployment = self._cursor.fetchone()

        if deployment is None:
            raise DeploymentNotFoundError(f'Deployment with ID {deployment_id} not found')

        host, port, status = deployment

        if status != DeploymentStatus.RUNNING:
            return False

        try:
            requests.get(f'http://{host}:{port}/ping')
            return True
        except requests.exceptions.ConnectionError:
            return False

    def check_and_update_deployments_statuses(self) -> None:
        """Check if deployment status.
        If status "running" is not confirmed, change status to "stopped"
        """

        self._cursor.execute(
            f'SELECT id, host, port FROM {self._DEPLOYMENTS_TABLE} '
            f'WHERE status = "{str(DeploymentStatus.RUNNING)}"'
        )
        running_local_deployments = self._cursor.fetchall()

        for deployment_id, host, port in running_local_deployments:

            try:
                requests.get(
                    url=f'http://{host}:{port}/ping',
                    timeout=self._GCP_INSTANCE_CONNECTION_TIMEOUT // 5
                )
            except requests.exceptions.ConnectionError:
                self._cursor.execute(
                    f'UPDATE {self._DEPLOYMENTS_TABLE} '
                    f'SET host = ?, port = ?, status = ? '
                    f'WHERE id = "{deployment_id}"',
                    (None, None, str(DeploymentStatus.STOPPED))
                )

            self._conn.commit()

    def _connect_db(self) -> None:
        """Connect to deploy database.

        Create deployments table and open connection to database.
        """

        self._conn = sqlite3.connect(self._DEPLOY_DB, check_same_thread=False)
        self._cursor = self._conn.cursor()

        columns_description = ', '.join([
            col_name + ' ' + col_type for col_name, col_type in self._deploy_table_schema.items()
        ])

        self._cursor.execute(
            f'CREATE TABLE IF NOT EXISTS {self._DEPLOYMENTS_TABLE} ({columns_description})'
        )

    def _next_id(self) -> int:
        """Get value that is one more than current maximum id"""

        self._cursor.execute(f'SELECT IFNULL(MAX(id), 0) FROM {self._DEPLOYMENTS_TABLE}')
        deploy_id = self._cursor.fetchone()[0] + 1

        return deploy_id

    def _insert_new_deployment_in_db(
            self, project_id: int, model_id: Text, model_version: Text, model_uri: Text,
            host: Text, port: int, pid: int, instance_name: Text, deployment_type: Text
    ) -> int:
        """Insert new deployment record in database.
        Args:
            project_id {int}: project id
            model_id {Text}:  model id (name)
            model_version {Text}: model version
            model_uri {Text}: path to model package
            host {Text}: host address
            port {int}: port number
            pid {int}: deployment process number
            instance_name {Text}: name of instance
            deployment_type {Text}: deployment type
        Returns:
            int: id of insert deployment record
        Notes:
            * pid: is some positive integer in case of local deployment
                and -1, if deployment type is remote;
            * instance_name: is empty string for local and  non-empty
                string (name of remote virtual machine) for remote deployment.
        """
        # pylint: disable=too-many-arguments

        deployment_id = self._next_id()
        creation_datetime = get_rfc3339_time()
        self._cursor.execute(
            f'INSERT INTO {self._DEPLOYMENTS_TABLE} '
            f'(id, project_id, model_id, version, model_uri, host, port, '
            f'pid, instance_name, type, created_at, last_updated_at, status) '
            f'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (
                deployment_id, project_id, model_id, model_version, model_uri,
                host, port, pid, instance_name, deployment_type, creation_datetime,
                creation_datetime, str(DeploymentStatus.RUNNING)
            )
        )
        self._conn.commit()

        return deployment_id
