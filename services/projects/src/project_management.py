"""
This module contains class for projects management - ProjectManager.
It allows to create, run, stop and delete projects.
"""

# pylint: disable=wrong-import-order,invalid-name,redefined-builtin

import os
import psutil
import psycopg2
import psycopg2.errors
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import shutil
import subprocess
from typing import Any, Dict, List, Set, Text

from common.types import StrEnum
from common.utils import get_rfc3339_time, kill, is_remote
from projects.src.config import Config
from projects.src.utils import process_stat


class NoFreePortsError(Exception):
    """No free ports."""


class BadProjectNameError(Exception):
    """Bad project name."""


class ProjectAlreadyExistsError(Exception):
    """Project already exists."""


class ProjectIsAlreadyRunningError(Exception):
    """Project is already running."""


class ProjectNotFoundError(Exception):
    """Project not found."""


class BadSQLiteTableSchema(Exception):
    """Bad SQLite table schema"""


class ProjectStatus(StrEnum):
    """Project status enum."""

    RUNNING = 'running'
    TERMINATED = 'terminated'
    ARCHIVED = 'archived'


class ProjectsDBSchema:

    CONFIG = Config()
    DB_NAME = CONFIG.get('PROJECTS_DB_NAME')
    PROJECTS_TABLE = 'project'

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

        self.create_projects_table()

    def create_projects_table(self):

        schema = {
            'id': 'SERIAL PRIMARY KEY ',
            'name': 'TEXT UNIQUE',
            'description': 'TEXT DEFAULT NULL',
            'port': 'INTEGER UNIQUE',
            'path': 'TEXT',
            'archived': 'INT',
            'created_at': 'TEXT',
            'pid': 'INT'  # subprocess IF for mlflow tracking server
        }

        self._create_table(self.PROJECTS_TABLE, schema)

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

    def _create_table(self, table_name: Text, table_schema: Dict):

        columns_description = ', '.join([
            col_name + ' ' + col_type for col_name, col_type in table_schema.items()
        ])

        self._cursor.execute(
            f'CREATE TABLE IF NOT EXISTS {table_name} ({columns_description})'
        )

        self._connection.commit()


class ProjectManager:
    """Project manager.
    Allows to create, run, terminate and delete projects.
    """
    # pylint: disable=too-many-instance-attributes
    def __init__(self):

        self.CONFIG = Config()
        self._WORKSPACE = self.CONFIG.get('WORKSPACE')
        self._PROJECTS_DB_NAME = self.CONFIG.get('PROJECTS_DB_NAME')
        self._TRACKING_DB = os.path.join(self._WORKSPACE, self._PROJECTS_DB_NAME)
        self._ARTIFACTS_STORE = self.CONFIG.get('ARTIFACT_STORE')

        if self._ARTIFACTS_STORE is None:
            raise EnvironmentError('Failed because env var ARTIFACT_STORE is not set')

        self._ports_range = self._get_ports_range()

        self._connection = psycopg2.connect(
            database=self.CONFIG.get('PROJECTS_DB_NAME'),
            host=self.CONFIG.get('DB_HOST'),
            port=self.CONFIG.get('DB_PORT'),
            user=self.CONFIG.get('DB_USER'),
            password=self.CONFIG.get('DB_PASSWORD')
        )
        self._cursor = self._connection.cursor()

    def create_project(self, name: Text, description: Text = '') -> int:
        """Create new project: create project folder in workspace
        and assign tracking server port for the project.
        Args:
            name {Text}: name of project
            description {Text}: project description
        Returns:
            int: project id
        """

        if not isinstance(name, str) or len(name) == 0:
            raise BadProjectNameError(f'Bad project name: "{name}" of type {type(name)}')

        if self._project_name_exists(name):

            project = self.get_project_by_name(name)
            archived = project.get('archived')
            additional_error_msg = ''

            if archived is True:
                additional_error_msg = ' - archived'

            raise ProjectAlreadyExistsError(
                f'Project "{name}" already exists {additional_error_msg}')

        port = self._get_free_port()

        self._cursor.execute(
            f'INSERT INTO {ProjectsDBSchema.PROJECTS_TABLE} '
            f'(name, description, port, archived, created_at, pid) '
            f'VALUES (%s,%s,%s,%s,%s,%s) '
            f'RETURNING id',
            (name, description, port, 0, get_rfc3339_time(), -1)
        )

        project_id = self._cursor.fetchone()[0]
        print('project_id:', project_id)
        project_path = os.path.join(self._WORKSPACE, str(project_id))
        os.makedirs(project_path, exist_ok=True)

        self._cursor.execute(
            f'UPDATE {ProjectsDBSchema.PROJECTS_TABLE} '
            f'SET path = %s '
            f'WHERE id = {project_id}',
            (project_path, )
        )

        self._connection.commit()

        return project_id

    def update_project_name(self, id: int, new_name: Text) -> None:
        """Update project name
        Args:
            id {int}: project id
            new_name {Text}: project name
        """

        self._update_project_field(id, 'name', new_name)

    def update_project_description(self, id: int, new_description: Text) -> None:
        """Update project description
        Args:
            id {int}: project id
            new_description {Text}: project description
        """

        self._update_project_field(id, 'description', new_description)

    def delete_project(self, id: int) -> None:
        """Delete project.
        Args:
            int {Text}: project id
        """

        if not self._project_id_exists(id):
            raise ProjectNotFoundError(f'Project with ID {id} not found')

        self._cursor.execute(f'SELECT path FROM {ProjectsDBSchema.PROJECTS_TABLE} WHERE id = {id}')
        project_path = self._cursor.fetchone()[0]
        shutil.rmtree(project_path, ignore_errors=True)

        self._cursor.execute(f'DELETE from {ProjectsDBSchema.PROJECTS_TABLE} WHERE id = {id}')
        self._connection.commit()

    def list_projects(self) -> List[Dict]:
        """Get list of existed projects.
        Returns:
            List: list of project dictionaries:
                    [
                        {
                            'id': <project_id>,
                            'name': <project_name>,
                            'description': <project_description>,
                            'status': <running|terminated|archived>,
                            'mlflowUri': <http://<host>:<port>,
                            'description': '',
                            'createdBy': 0,
                            'createdAt': <timestamp>
                            'path': <path_to_project_folder_in_workspace>
                        },
                        ...
                    ]
        """

        self._cursor.execute(f'SELECT * FROM {ProjectsDBSchema.PROJECTS_TABLE}')
        projects = []

        for rec in self._cursor.fetchall():

            id, name, description, port, path, archived, created_at, pid = rec
            is_running = self._is_running(id)
            status = ProjectStatus.TERMINATED

            if is_running:
                status = ProjectStatus.RUNNING
            elif archived:
                status = ProjectStatus.ARCHIVED

            projects.append({
                'id': id,
                'name': name,
                'description': description,
                'status': str(status),
                'mlflowUri': f'http://{self.CONFIG.get("HOST_IP")}:{port}',
                'createdBy': 0,
                'createdAt': created_at,
                'path': path
            })

        return projects

    def get_project(self, id: int) -> Dict:
        """Get project info.
        Args:
            id {int}: project id
        Returns:
            Dict - project info dictionary:
                        {
                            'id': <project_id>,
                            'name': <project_name>,
                            'status': <running|terminated|archived>,
                            'mlflowUri': <http://<host>:<port>,
                            'description': '',
                            'createdBy': 0,
                            'createdAt': <timestamp>
                            'path': <path_to_project_folder_in_workspace>
                        }
        """

        if not self._project_id_exists(id):
            raise ProjectNotFoundError(f'Project with ID {id} not found')

        projects_list = self.list_projects()
        projects = {project['id']: project for project in projects_list}

        return projects.get(id)

    def get_project_by_name(self, name: Text) -> Dict:
        """Get project info by name.
        Args:
            name {Text}: project name
        Returns:
            Dict: project info dictionary:
                        {
                            'id': <project_id>,
                            'name': <project_name>,
                            'port': <port>,
                            'is_running': <True|False>,
                            'path': <path_to_project_folder_in_workspace>,
                            'archived': <True|False>
                        }
        """

        if not self._project_name_exists(name):
            raise ProjectNotFoundError(f'Project with ID {id} not found')

        self._cursor.execute(f'SELECT * FROM {ProjectsDBSchema.PROJECTS_TABLE} WHERE name = \'{name}\'')
        rec = self._cursor.fetchone()
        project = {
            'id': rec[0],
            'name': rec[1],
            'port': rec[2],
            'is_running': self._is_running(rec[0]),
            'path': rec[3],
            'archived': rec[4] == 1
        }

        return project

    def get_internal_tracking_uri(self, project_id: int) -> Text:
        """Get tracking uri by project id.
        Args:
            project_id {int}: project id
        Returns:
            Text: MLflow tracking server uri for the project
        """

        return self.get_project(project_id).get('mlflowUri').replace('https', 'http')

    def archive(self, project_id: int) -> None:
        """Archive project.
        Args:
            project_id {Text}: project id
        """

        self._set_archived_status(project_id)

    def restore(self, project_id: int) -> None:
        """Restore project.
        Args:
            project_id {Text}: project id
        """

        self._set_archived_status(project_id, archive=False)

    def run(self, project_id: int) -> bool:
        """Run tracking server for project.
        Args:
            project_id {int}: project id
        Returns:
            bool: True if server run, otherwise False
        """

        if self._is_running(project_id):
            raise ProjectIsAlreadyRunningError(f'Project with ID {project_id} is already running')

        if not self._project_id_exists(project_id):
            raise ProjectNotFoundError(f'Project with ID {project_id} not found')

        project_info = self.get_project(project_id)
        port = project_info.get('mlflowUri').split(':')[-1]
        path = project_info.get('path')
        project_mlflow_db = 'sqlite:///' + os.path.join(path, 'mlflow.db')

        if is_remote(self._ARTIFACTS_STORE):
            default_artifact_root = os.path.join(self._ARTIFACTS_STORE, f'{project_id}/mlruns')
        else:
            default_artifact_root = os.path.join(self._WORKSPACE, str(project_id), self._ARTIFACTS_STORE)

        access_log = os.path.join(path, 'access.log')
        errors_log = os.path.join(path, 'errors.log')
        mlflow_stdout_log = os.path.join(path, 'mlflow_stdout.log')

        tracking_server_process = subprocess.Popen(
            [
                f'GUNICORN_CMD_ARGS="--access-logfile={access_log} --error-logfile={errors_log} '
                f'--log-level=debug" '
                f'mlflow server '
                f'--backend-store-uri {project_mlflow_db} '
                f'--default-artifact-root {default_artifact_root} '
                f'--host 0.0.0.0 --port {port}  '
                f'--workers {self.CONFIG.get("TRACKING_SERVER_WORKERS")} '
                f'2>&1 | tee -a {mlflow_stdout_log}'
            ],
            shell=True
        )

        self._cursor.execute(
            f'UPDATE {ProjectsDBSchema.PROJECTS_TABLE} '
            f'SET pid = %s '
            f'WHERE id = {project_id}',
            (tracking_server_process.pid,)
        )
        self._connection.commit()

        return tracking_server_process.poll() is None

    def terminate(self, project_id: int) -> None:
        """Run tracking server for project.
        Args:
            project_id {int}: project id
        """

        self._cursor.execute(f'SELECT pid FROM {ProjectsDBSchema.PROJECTS_TABLE} WHERE id = {project_id}')
        project_pid = self._cursor.fetchone()

        if project_pid:

            pid = project_pid[0]

            if pid > 0:

                kill(pid)
                self._cursor.execute(
                    f'UPDATE {ProjectsDBSchema.PROJECTS_TABLE} '
                    f'SET pid = %s '
                    f'WHERE id = {project_id}',
                    (-1,)
                )
                self._connection.commit()

    def running_projects_stat(self) -> List[Dict]:
        """Get statistics by running projects.
        Returns:
            List[Dict]: list or projects stat:
                [
                    {
                        'id': <project_id>,
                        'name': <project_name>,
                        'stat': {<statistics>}
                ]
        """

        stat = []

        self._cursor.execute(f'SELECT id, pid FROM {ProjectsDBSchema.PROJECTS_TABLE} WHERE pid <> -1')
        rows = self._cursor.fetchall()

        for project_id, pid in rows:

            stat.append({
                'id': project_id,
                'name': self.get_project(project_id).get('name'),
                'stat': process_stat(pid)
            })

        return stat

    def _get_ports_range(self) -> Set:
        """Get available ports range.
        Returns:
            Set: set of port numbers
        """

        ports_range = self.CONFIG.get('TRACKING_SERVER_PORTS')

        if ports_range is None:
            raise EnvironmentError(
                'Failed because env var TRACKING_SERVER_PORTS is not set')

        start_port, end_port = list(map(int, ports_range.split('-')))

        return set(range(start_port, end_port + 1))

    @property
    def workspace(self) -> Text:
        """Get workspace path."""
        return self._WORKSPACE

    def _get_free_port(self) -> int:
        """Get free port from range
        Returns:
            int: free port
        """

        self._cursor.execute(f'SELECT port FROM {ProjectsDBSchema.PROJECTS_TABLE}')
        assigned_ports = {record[0] for record in self._cursor.fetchall()}

        free_ports = self._ports_range.difference(assigned_ports)

        if len(free_ports) == 0:
            raise NoFreePortsError('No free ports!')

        return min(free_ports)

    def _project_name_exists(self, name: Text) -> bool:
        """Check if project name already exists.
        Args:
            name {Text}: name of project
        Returns:
            bool: True if project name exists, False otherwise
        """

        self._cursor.execute(f'SELECT * FROM {ProjectsDBSchema.PROJECTS_TABLE} WHERE name = \'{name}\'')
        project = self._cursor.fetchone()

        return project is not None

    def _project_id_exists(self, id: int) -> bool:
        """Check if project id already exists.
        Args:
            id {int}: project id
        Returns:
            bool: True if project id exists, False otherwise
        """

        self._cursor.execute(f'SELECT * FROM {ProjectsDBSchema.PROJECTS_TABLE} WHERE id = {id}')
        records = self._cursor.fetchall()

        return len(records) != 0

    def _is_running(self, project_id: int) -> bool:
        """Check if tracking server for the project is running.
        Args:
            project_id {int}: project idText
        Returns:
            bool: True if tracking server is running, otherwise False
        """

        pid = self._get_pid(project_id)

        if not pid:
            raise ProjectNotFoundError(f'Project with ID {project_id} not found')

        return psutil.pid_exists(pid)

    def _set_archived_status(self, project_id: int, archive: bool = True) -> None:
        """Set project archived status.
        Args:
            project_id {int}: project id
            archive {bool}: status flag
        """

        if not self._project_id_exists(project_id):
            raise ProjectNotFoundError(f'Project with ID {project_id} not found')

        self._cursor.execute(
            f'UPDATE {ProjectsDBSchema.PROJECTS_TABLE} SET archived = %s WHERE id = {project_id}',
            (1 if archive is True else 0,)
        )
        self._connection.commit()

    def _update_project_field(self, id: int, field: Text, value: Any) -> None:
        """Update project field.
        Args:
            id {int}: project_id
            field {Text}: field name
            value {Any}: new value
        """

        if not self._project_id_exists(id):
            raise ProjectNotFoundError(f'Project with ID {id} not found')

        self._cursor.execute(
            f'UPDATE {ProjectsDBSchema.PROJECTS_TABLE} '
            f'SET {field} = %s'
            f'WHERE id = {id}',
            (value,)
        )
        self._connection.commit()

    def _get_pid(self, project_id: int) -> int:
        """
        Get project's tracking server process pid.
        Args:
            project_id {int}: project id
        Returns:
            int: pid
        """

        self._cursor.execute(
            f'SELECT pid FROM {ProjectsDBSchema.PROJECTS_TABLE} WHERE id = {project_id}'
        )
        pid = self._cursor.fetchone()

        if pid:
            return pid[0]

