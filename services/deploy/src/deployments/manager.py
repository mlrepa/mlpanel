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


import json
import logging
import os
import psycopg2
import psycopg2.errors
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import requests
from typing import Dict, List, Optional, Text, Tuple

from common.types import StrEnum
from common.utils import is_model, ModelDoesNotExistError, is_remote, get_rfc3339_time,\
    get_utc_timestamp
from deploy.src.config import Config
from deploy.src.deployments.gcp import create_gcp_deployment, wait_gcp_host_ip, stop_gcp_deployment
from deploy.src.deployments.gcp_deploy_utils import generate_gcp_instance_name
from deploy.src.deployments.local import create_local_deployment, stop_local_deployment
from deploy.src.deployments.utils import get_schema_file_path, validate_data, \
    BadInputDataSchemaError, predict_data_to_mlflow_data_format, mlflow_model_predict,\
    schema_file_exists, tfdv_object_to_dict, read_tfdv_statistics, get_gcp_deployment_config,\
    get_local_deployment_config
from deploy.src.utils import local_model_uri_to_gs_blob, upload_local_mlflow_model_to_gs


logging.basicConfig(level=logging.DEBUG)


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


class DeployDbSchema:

    CONFIG = Config()
    DB_NAME = CONFIG.get('DEPLOY_DB_NAME')
    DEPLOYMENTS_TABLE = 'deployment'
    INCOMING_DATA_TABLE = 'incoming_data'

    def __init__(self):

        self._create_db()

        self._connection = psycopg2.connect(
            database=self.CONFIG.get('PROJECTS_DB_NAME'),
            host=self.CONFIG.get('DB_HOST'),
            port=self.CONFIG.get('DB_PORT'),
            user=self.CONFIG.get('DB_USER'),
            password=self.CONFIG.get('DB_PASSWORD')
        )
        self._cursor = self._connection.cursor()

        self.create_deployments_table()
        self.create_incoming_data_table()

    def create_deployments_table(self):

        schema = {
            'id': 'SERIAL PRIMARY KEY',
            'project_id': 'INT',
            'model_id': 'TEXT',
            'version': 'TEXT',
            'model_uri': 'TEXT',
            'host': 'TEXT',
            'port': 'INT',
            'pid': 'INT',
            'instance_name': 'TEXT',
            'type': 'TEXT',
            'created_at': 'TEXT',
            'last_updated_at': 'TEXT',
            'status': 'TEXT'
        }
        self._create_table(self.DEPLOYMENTS_TABLE, schema)

    def create_incoming_data_table(self):

        schema = {
            'id': 'SERIAL PRIMARY KEY',
            'deployment_id': 'INT',
            'incoming_data': 'TEXT',  # TODO: как лучше сохранять данные, в каком формате?
            'timestamp': 'REAL',
            'is_valid': 'INT',
            'anomalies': 'TEXT'
        }
        self._create_table(self.INCOMING_DATA_TABLE, schema)

    def _create_table(self, table_name: Text, table_schema: Dict):

        columns_description = ', '.join([
            col_name + ' ' + col_type for col_name, col_type in table_schema.items()
        ])

        self._cursor.execute(
            f'CREATE TABLE IF NOT EXISTS {table_name} ({columns_description})'
        )

        self._connection.commit()

    def _create_db(self):

        connection = psycopg2.connect(
            host=self.CONFIG.get('DB_HOST'),
            port=self.CONFIG.get('DB_PORT'),
            user=self.CONFIG.get('DB_USER'),
            password=self.CONFIG.get('DB_PASSWORD')
        )
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = connection.cursor()

        try:
            cursor.execute(f'CREATE DATABASE {self.DB_NAME};')
        except psycopg2.errors.DuplicateDatabase:
            pass

        connection.close()


class Deployment:
    """
    Deployment.
    """

    def __init__(self, **deployment_config):

        self.config = deployment_config

    def up(self, model_uri: Text) -> Tuple[Text, int, int, Text]:
        """
        Up new deployment.
        Args:
            model_uri {Text}: model uri
        Returns:
            Tuple[Text, int, int, Text]: (host, port, pid, instance_name)
        """
        raise NotImplementedError('To be implemented')

    def stop(self, process_id: int, instance_name: Text) -> None:
        """
        Stop deployment.
        Args:
            process_id {int}: process id
            instance_name {Text}: instance name
        """
        raise NotImplementedError('To be implemented')

    def predict(self, model_uri: Text, host: Text, port: int, data: Text) \
            -> Tuple[int, Dict, Optional[requests.Response]]:

        """
        Predict data.
        Args:
            model_uri {Text}: model uri
            host {Text}: host ip or domain name
            port {int}: port number
            data {Text}: data to predict
        Returns:
            Tuple[int, Dict, Optional[requests.Response]]:
                (data_is_valid_flag, anomalies_dictionary, requests.Response or None)
        """

        logging.info('predict')

        self._check_model_exists(model_uri)

        schema_file_path = get_schema_file_path(model_uri)
        data_is_valid = -1
        anomalies = {}
        response = None

        if os.getenv('VALIDATE_ON_PREDICT') == 'true':
            data_is_valid, anomalies = validate_data(data, schema_file_path)

        if data_is_valid:
            converted_data = predict_data_to_mlflow_data_format(data)
            response = mlflow_model_predict(host, port, converted_data)

        return data_is_valid, anomalies, response

    def ping(self, host: Text, port: int) -> bool:
        """
        Ping deployment.
        Args:
            host {Text}: host ip or domain name
            port {int}: port number
        Returns:
            bool: True if deployment with host and port is reachable, otherwise False
        """

        logging.info(f'ping http://{host}:{port}')

        try:
            requests.get(f'http://{host}:{port}/ping')
            return True
        except requests.exceptions.ConnectionError:
            return False

    def schema(self, model_uri: Text) -> Dict:
        """
        Get deployment's model schema.
        Args:
            model_uri {Text}: model uri
        Returns:
            Dict: model schema.
        """

        logging.info(f'get schema for {model_uri}')

        schema_file_path = get_schema_file_path(model_uri)

        if schema_file_exists(schema_file_path):
            return tfdv_object_to_dict(read_tfdv_statistics(schema_file_path))
        else:
            return {}

    def _check_model_exists(self, model_uri: Text) -> None:
        """
        Check if model exists.
        Args:
            model_uri {Text}: model uri
        Raises:
            ModelDoesNotExistError: if model does not exists or is not MLflow model
        """

        if not is_model(model_uri):
            raise ModelDoesNotExistError(
                f'Model {model_uri} does not exist or is not MLflow model')


class LocalDeployment(Deployment):
    """
    Local deployment.
    """

    def up(self, model_uri: Text) -> Tuple[Text, int, int, Text]:
        """
        Up new deployment.
        Args:
            model_uri {Text}: model uri
        Returns:
            Tuple[Text, int, int, Text]: (host, port, pid, instance_name)
        """

        logging.info('up local deployment')

        self._check_model_exists(model_uri)

        instance_name = ''
        host = '0.0.0.0'
        process, port = create_local_deployment(model_uri)
        pid = process.pid

        return host, port, pid, instance_name

    def stop(self, process_id: int = None, instance_name: Text = None):
        """
        Stop deployment.
        Args:
            process_id {int}: process id
            instance_name {Text}: instance name
        """

        logging.info('stop local deployment')
        stop_local_deployment(process_id)


class GCPDeployment(Deployment):
    """
    GCP deployment.
    """

    def __init__(self, **deployment_config):

        super().__init__(**deployment_config)
        self._GCP_INSTANCE_CONNECTION_TIMEOUT = 30

    def up(self, model_uri: Text) -> Tuple[Text, int, int, Text]:
        """
        Up new deployment.
        Args:
            model_uri {Text}: model uri
        Returns:
            Tuple[Text, int, int, Text]: (host, port, pid, instance_name)
        """

        logging.info('up gcp deployment')

        self._check_model_exists(model_uri)

        pid = -1
        cached_model_uri = model_uri

        if not is_remote(model_uri):

            logging.info('local model, gcp deployment')
            cached_model_uri = os.path.join(
                'gs://', self.config.get('bucket'),
                local_model_uri_to_gs_blob(model_uri)
            )

            logging.info(f'cached_model_uri: {cached_model_uri}')

            if not is_model(cached_model_uri):
                logging.info('upload local model to gs bucket')
                upload_local_mlflow_model_to_gs(model_uri)

        instance_name = generate_gcp_instance_name()
        create_gcp_deployment(cached_model_uri, self.config, instance_name)
        port = self.config.get('port')
        host = wait_gcp_host_ip(instance_name, self.config, self._GCP_INSTANCE_CONNECTION_TIMEOUT)

        return host, port, pid, instance_name

    def stop(self, process_id: int = None, instance_name: Text = None):
        """
        Stop deployment.
        Args:
            process_id {int}: process id
            instance_name {Text}: instance name
        """

        logging.info(f'stop gcp instance {instance_name}')
        stop_gcp_deployment(instance_name, self.config)


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
        self.CONFIG = Config()
        self._WORKSPACE = self.CONFIG.get('WORKSPACE')
        self._GCP_CONFIG = self.CONFIG.get_gcp_config()
        self._GCP_INSTANCE_CONNECTION_TIMEOUT = 30

        self._connection = psycopg2.connect(
            database=self.CONFIG.get('PROJECTS_DB_NAME'),
            host=self.CONFIG.get('DB_HOST'),
            port=self.CONFIG.get('DB_PORT'),
            user=self.CONFIG.get('DB_USER'),
            password=self.CONFIG.get('DB_PASSWORD')
        )
        self._cursor = self._connection.cursor()

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

        deployment = self._make_deployment(deployment_type)
        host, port, pid, instance_name = deployment.up(model_uri)

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
            f'SELECT type, model_uri, status '
            f'FROM {DeployDbSchema.DEPLOYMENTS_TABLE} '
            f'WHERE id = {deployment_id}'
        )
        deployment_row = self._cursor.fetchone()

        if deployment_row is None:
            raise DeploymentNotFoundError(f'Deployment with ID {deployment_id} not found')

        deployment_type, model_uri, status = deployment_row

        if status == DeploymentStatus.RUNNING:
            return

        deployment = self._make_deployment(deployment_type)
        host, port, pid, instance_name = deployment.up(model_uri)

        self._cursor.execute(
            f'UPDATE {DeployDbSchema.DEPLOYMENTS_TABLE} '
            f'SET host = %s, port = %s, status = %s, pid = %s, instance_name = %s, last_updated_at = %s '
            f'WHERE id = {deployment_id}',
            (host, port, str(DeploymentStatus.RUNNING), pid, instance_name, get_rfc3339_time())
        )
        self._connection.commit()

    def stop(self, deployment_id: int) -> None:
        """Stop deployment.
        Args:
            deployment_id {int}: deployment id
        """

        self._cursor.execute(
            f'SELECT status, type, pid, instance_name '
            f'FROM {DeployDbSchema.DEPLOYMENTS_TABLE} '
            f'WHERE id = {deployment_id} AND '
            f'      status <> \'{str(DeploymentStatus.DELETED)}\''
        )
        deployment_row = self._cursor.fetchone()

        if deployment_row is None:
            raise DeploymentNotFoundError(f'Deployment with ID {deployment_id} not found')

        status, deployment_type, pid, instance_name = deployment_row

        if status == DeploymentStatus.STOPPED:
            return

        deployment = self._make_deployment(deployment_type)
        deployment.stop(pid, instance_name)

        self._cursor.execute(
            f'UPDATE {DeployDbSchema.DEPLOYMENTS_TABLE} '
            f'SET status = %s, host = %s, port = %s, last_updated_at = %s '
            f'WHERE id = {deployment_id}',
            (str(DeploymentStatus.STOPPED), None, None, get_rfc3339_time())
        )
        self._connection.commit()

    def delete(self, deployment_id: int) -> None:
        """Delete deployment (mark as deleted.
        Args:
            deployment_id {int}: deployment id
        """

        self.stop(deployment_id)
        self._cursor.execute(
            f'UPDATE {DeployDbSchema.DEPLOYMENTS_TABLE} '
            f'SET status = %s, host = %s, port = %s, last_updated_at = %s '
            f'WHERE id = {deployment_id}',
            (str(DeploymentStatus.DELETED), None, None, get_rfc3339_time())
        )
        self._connection.commit()

    def predict(self, deployment_id: int, data: Text) -> requests.Response:
        """Predict data on deployment.
        Args:
            deployment_id {int}: deployment id
            data {Text}: data to predict
        """

        self._cursor.execute(
            f'SELECT model_uri, host, port, type '
            f'FROM {DeployDbSchema.DEPLOYMENTS_TABLE} '
            f'WHERE id = {deployment_id} AND '
            f'      status <> \'{str(DeploymentStatus.DELETED)}\''
        )
        deployment_row = self._cursor.fetchone()

        if deployment_row is None:
            raise DeploymentNotFoundError(f'Deployment with ID {deployment_id} not found')

        model_uri, host, port, deployment_type = deployment_row
        deployment = self._make_deployment(deployment_type)
        data_is_valid, anomalies, response = deployment.predict(model_uri, host, port, data)

        self._cursor.execute(
            f'INSERT INTO {DeployDbSchema.INCOMING_DATA_TABLE} '
            f'(deployment_id,incoming_data,timestamp,is_valid,anomalies) '
            f'VALUES (%s,%s,%s,%s,%s)',
            (deployment_id, data, get_utc_timestamp(), int(data_is_valid), json.dumps(anomalies))
        )
        self._connection.commit()

        if not data_is_valid:
            raise BadInputDataSchemaError({'anomalies': anomalies})

        return response

    def list(self) -> List[Dict]:
        """Get list of deployments info.
        Returns:
            List[Dict]
        """

        self._cursor.execute(
            f'SELECT id, project_id, model_id, version, model_uri, '
            f'type, created_at, instance_name, status, host, port '
            f'FROM {DeployDbSchema.DEPLOYMENTS_TABLE} '
            f'WHERE status <> \'{str(DeploymentStatus.DELETED)}\''
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
            f'SELECT host, port, status, type '
            f'FROM {DeployDbSchema.DEPLOYMENTS_TABLE} '
            f'WHERE id = {deployment_id}'
        )
        deployment_row = self._cursor.fetchone()

        if deployment_row is None:
            raise DeploymentNotFoundError(f'Deployment with ID {deployment_id} not found')

        host, port, status, deployment_type = deployment_row

        if status != DeploymentStatus.RUNNING:
            return False

        deployment = self._make_deployment(deployment_type)

        return deployment.ping(host, port)

    def deployment_schema(self, deployment_id: int) -> Dict:

        self._cursor.execute(
            f'SELECT model_uri, type '
            f'FROM {DeployDbSchema.DEPLOYMENTS_TABLE} '
            f'WHERE id = {deployment_id} AND status <> \'{str(DeploymentStatus.DELETED)}\''
        )
        deployment_row = self._cursor.fetchone()

        if not deployment_row:
            raise DeploymentNotFoundError(f'Deployment with ID {deployment_id} not found')

        model_uri, deployment_type = deployment_row
        deployment = self._make_deployment(deployment_type)

        return deployment.schema(model_uri)

    def check_and_update_deployments_statuses(self) -> None:
        """Check if deployment status.
        If status "running" is not confirmed, change status to "stopped"
        """

        self._cursor.execute(
            f'SELECT id, host, port FROM {DeployDbSchema.DEPLOYMENTS_TABLE} '
            f'WHERE status = \'{str(DeploymentStatus.RUNNING)}\''
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
                    f'UPDATE {DeployDbSchema.DEPLOYMENTS_TABLE} '
                    f'SET host = %s, port = %s, status = %s '
                    f'WHERE id = {deployment_id}',
                    (None, None, str(DeploymentStatus.STOPPED))
                )

            self._connection.commit()

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

        creation_datetime = get_rfc3339_time()
        self._cursor.execute(
            f'INSERT INTO {DeployDbSchema.DEPLOYMENTS_TABLE} '
            f'(project_id, model_id, version, model_uri, host, port, '
            f'pid, instance_name, type, created_at, last_updated_at, status) '
            f'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) '
            f'RETURNING id',
            (
                project_id, model_id, model_version, model_uri,
                host, port, pid, instance_name, deployment_type, creation_datetime,
                creation_datetime, str(DeploymentStatus.RUNNING)
            )
        )
        deployment_id = self._cursor.fetchone()[0]

        self._connection.commit()

        return deployment_id

    @staticmethod
    def _make_deployment(deployment_type):

        if deployment_type == DeploymentType.LOCAL:
            deployment_config = get_local_deployment_config()
            return LocalDeployment(**deployment_config)

        elif deployment_type == DeploymentType.GCP:
            # TODO: think about config.get_gcp_confgi() -> GCP_CONFIG
            deployment_config = get_gcp_deployment_config()
            return GCPDeployment(**deployment_config)

        else:
            raise InvalidDeploymentType(f'Invalid deployment type: {deployment_type}')

