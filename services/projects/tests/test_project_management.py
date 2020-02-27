import os
import pytest
import shutil
import sqlite3

from projects.src import config
from projects.src.project_management import ProjectManager, BadProjectNameError, \
    ProjectAlreadyExistsError, ProjectNotFoundError


class TestTrackingServerManager:

    def setup_method(self):

        os.makedirs(config.WORKSPACE, exist_ok=True)
        self.tsm = ProjectManager()

    def teardown_method(self):

        shutil.rmtree(config.WORKSPACE, ignore_errors=True)

    def test_init(self):

        assert os.path.exists(os.path.join(config.WORKSPACE, config.PROJECTS_DB_NAME)) is True

    def test_create_project(self):

        project = 'New Project'
        self.tsm.create_project(project)

        conn = sqlite3.connect(os.path.join(config.WORKSPACE, config.PROJECTS_DB_NAME))
        cur = conn.cursor()
        cur.execute('SELECT * FROM project')

        project_id, project_name, project_description, port, path, archived, created_at, pid = cur.fetchone()

        assert project_id == 1
        assert project_name == project
        assert project_description == ''
        assert isinstance(port, int)
        assert path == os.path.join(config.WORKSPACE, '1')
        assert os.path.exists(path) is True
        assert archived == 0
        assert pid == -1

        conn.close()

    def test_create_project_already_exists(self):

        project = 'New Project'
        self.tsm.create_project(project)

        with pytest.raises(ProjectAlreadyExistsError):
            self.tsm.create_project(project)

    @pytest.mark.parametrize(
        'name',
        [1, None, object]
    )
    def test_create_project_bad_name(self, name):

        with pytest.raises(BadProjectNameError):
            self.tsm.create_project(name)

    def test_list_projects_no_projects(self):

        assert self.tsm.list_projects() == list()

    def test_list_projects(self):

        projects = ['proj1', 'proj2', 'proj3']

        for proj in projects:
            self.tsm.create_project(proj)

        assert set(projects) == set([p.get('name') for p in self.tsm.list_projects()])

    def test_get_project_no_projects(self):

        with pytest.raises(ProjectNotFoundError):
            assert self.tsm.get_project(id=0)

    def test_archive(self):

        project_name = 'New Project'
        project_id = self.tsm.create_project(project_name)
        self.tsm.archive(project_id)
        project_info = self.tsm.get_project(project_id)

        assert project_info['status'] == 'archived'

    def test_run_terminate_server(self):

        project_name = 'Running Project'

        project_id = self.tsm.create_project(project_name)
        self.tsm.run(project_id)

        assert self.tsm._is_running(project_id) is True

        self.tsm.terminate(project_id)

        assert self.tsm._is_running(project_id) is False




