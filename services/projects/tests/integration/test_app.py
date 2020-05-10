from http import HTTPStatus
import pytest
import shutil
from starlette.testclient import TestClient
import requests
import time
from typing import Text

from projects.src import config, app


@pytest.fixture(scope='module')
def client():
    
    app.init()
    
    return TestClient(app.app)


@pytest.fixture(scope='module')
def tracking_server_run_timeout():

    return 20


def wait_loading(url: Text, timeout: int = 10):
    waiting_time = timeout
    tracking_server_loaded = False

    while True:
        try:
            r = requests.get(url)

            if r.status_code == HTTPStatus.OK:
                tracking_server_loaded = True
                break

        except requests.ConnectionError:
            pass

        time.sleep(1)
        waiting_time -= 1

        if waiting_time <= 0:
            break

    return tracking_server_loaded


def teardown_module():
    shutil.rmtree(config.Config().get('WORKSPACE'), ignore_errors=True)


# /projects (GET) - list project
# curl -X GET "http://localhost:8080/projects" -H "accept: application/json"

def test_list_projects(client):
    projects = client.get('/projects').json()
    assert isinstance(projects, list)
    assert len(projects) == 0


# /projects (POST) - create project
# curl -X POST "http://localhost:8080/projects" -H "accept: */*" -H "Content-Type: multipart/form-data" -F "project=new"


def test_create_project(client):
    response = client.post('/projects', data={'name': 'new_project'}).json()
    assert response.get('id') == 1
    assert response.get('name') == 'new_project'
    assert response.get('status') == 'terminated'
    assert response.get('mlflowUri') == 'http://0.0.0.0:5000'


def test_create_duplicate_project(client):
    client.post('/projects', data={'name': 'dup_proj'}).json()
    response = client.post('/projects', data={'name': 'dup_proj'}).json()

    assert response.get('code') == '400'
    assert 'Project "dup_proj" already exists' in response.get('message')


# /projects/<int:id> (GET) - get project by id
# curl -X GET "http://localhost:8080/projects/1" -H "accept: application/json"


def test_get_project(client):
    project = client.get('/projects/1').json()

    assert project.get('id') == 1
    assert project.get('name') == 'new_project'
    assert project.get('status') == 'terminated'
    assert project.get('mlflowUri') == 'http://0.0.0.0:5000'


def test_get_nonexistent_project(client):
    response = client.get('/projects/1000').json()

    assert response.get('code') == '404'
    assert 'Project with ID 1000 not found' in response.get('message')


# /projects (DELETE) - delete project
# curl -X DELETE "http://localhost:8080/projects/1" -H "accept: */*"


def test_delete_project(client):
    response = client.delete('/projects/2')

    assert response.status_code == 200


def test_delete_nonexistent_project(client):
    response = client.delete('/projects/1000').json()

    assert response.get('code') == '404'
    assert 'Project with ID 1000 not found' in response.get('message')


# /projects/<int:id>/healthcheck
# curl -X GET "http://localhost:8080/projects/1/healthcheck" -H "accept: */*"


def test_project_healthcheck(client):
    response = client.get('/projects/1/healthcheck')

    assert response.status_code == 400


def test_nonexistent_project_healthcheck(client):
    response = client.get('/projects/1000/healthcheck')
    response_json = response.json()

    assert response.status_code == 404
    assert 'Project with ID 1000 not found' in response_json.get('message')


# /projects/<int:id>/run
# curl -X PUT "http://localhost:8080/projects/1/run" -H "accept: */*"

def test_run_project(client):
    response = client.put('/projects/1/run')

    assert response.status_code == 200

    healthcheck_response = client.get('/projects/1/healthcheck')

    assert healthcheck_response.status_code == 200


def test_run_nonexistent_project(client):
    response = client.put('/projects/1000/run')
    response_json = response.json()

    assert response.status_code == 404
    assert 'Project with ID 1000 not found' in response_json.get('message')


def test_try_run_already_running_project(client):
    response = client.put('/projects/1/run')
    response_json = response.json()

    assert response.status_code == 409
    assert 'Project with ID 1 is already running' in response_json.get('message')


# /projects/<int:id>/terminate
# curl -X PUT "http://localhost:8080/projects/1/terminate" -H "accept: */*"


def test_terminate_project(client):
    response = client.put('/projects/1/terminate')

    assert response.status_code == 200


# /projects/<int:id>/archive
# curl -X PUT "http://localhost:8080/projects/1/archive" -H "accept: */*"


def test_archive_project(client):
    response = client.put('/projects/1/archive')
    assert response.status_code == 200


def test_archive_nonexistent_project(client):
    response = client.put('/projects/1000/archive')
    response_json = response.json()

    assert response.status_code == 404
    assert 'Project with ID 1000 not found' in response_json.get('message')


# /projects/<int:id>restore
# curl -X PUT "http://localhost:8080/projects/1/restore" -H "accept: */*"


def test_restore_project(client):
    response = client.put('/projects/1/restore')
    assert response.status_code == 200


def test_restore_nonexistent_project(client):
    response = client.put('/projects/1000/restore')
    response_json = response.json()

    assert response.status_code == 404
    assert 'Project with ID 1000 not found' in response_json.get('message')


# /experiments

def test_list_experiments_not_running(client):
    response = client.get('/experiments?project_id=1')
    assert response.status_code == 500


def test_list_experiments_nonexistent_project(client):
    response = client.get('/experiments?project_id=1000')
    response_json = response.json()

    assert response.status_code == 404
    assert 'Project with ID 1000 not found' in response_json.get('message')


def test_list_experiments(client, tracking_server_run_timeout):
    client.put('/projects/1/run')

    assert wait_loading('http://0.0.0.0:5000', tracking_server_run_timeout) is True

    response = client.get('/experiments?project_id=1').json()

    assert len(response) == 1

    experiment = response[0]

    assert experiment['id'] == '0'

    client.put('/projects/1/terminate')


def test_get_experiment_not_running(client):
    response = client.get('/experiments/1?project_id=1')
    assert response.status_code == 500


def test_get_experiment_nonexistent_project(client):
    response = client.get('/experiments/1?project_id=1000')
    response_json = response.json()

    assert response.status_code == 404
    assert 'Project with ID 1000 not found' in response_json.get('message')


# /runs

def test_list_runs_not_running(client):
    response = client.get('/runs?project_id=1&experiment_id=1')
    assert response.status_code == 500


def test_list_runs_nonexistent_project(client):
    response = client.get('/runs?project_id=1000&experiment_id=1')
    response_json = response.json()

    assert response.status_code == 404
    assert 'Project with ID 1000 not found' in response_json.get('message')


def test_list_runs(client, tracking_server_run_timeout):
    client.put('/projects/1/run')

    assert wait_loading('http://0.0.0.0:5000', tracking_server_run_timeout) is True

    response = client.get('/runs?project_id=1&experiment_id=0').json()

    assert response == []

    client.put('/projects/1/terminate')


def test_get_run_not_running(client):
    response = client.get('/runs/1?project_id=1&experiment_id=1')
    assert response.status_code == 500


def test_get_run_nonexistent_project(client):
    response = client.get('/runs/1?project_id=1000&experiment_id=1')
    response_json = response.json()

    assert response.status_code == 404
    assert 'Project with ID 1000 not found' in response_json.get('message')


# /models

def test_list_models_not_running(client):
    response = client.get('/registered-models?project_id=1')
    assert response.status_code == 500


def test_list_models_nonexistent_project(client):
    response = client.get('/registered-models?project_id=1000')
    response_json = response.json()

    assert response.status_code == 404
    assert 'Project with ID 1000 not found' in response_json.get('message')


def test_list_models(client, tracking_server_run_timeout):
    client.put('/projects/1/run')

    assert wait_loading('http://0.0.0.0:5000', tracking_server_run_timeout) is True

    response = client.get('/registered-models?project_id=1').json()

    assert response == []

    client.put('/projects/1/terminate')


def test_get_model_not_running(client):
    response = client.get('/registered-models/Model?project_id=1')
    assert response.status_code == 500


def test_get_model_nonexistent_project(client):
    response = client.get('/registered-models/Model?project_id=1000')
    response_json = response.json()

    assert response.status_code == 404
    assert 'Project with ID 1000 not found' in response_json.get('message')


# /artifacts

def test_list_artifacts_not_running(client):
    response = client.get('/artifacts?project_id=1&run_id=79eac25d801f41f0baa68d322679f12')
    assert response.status_code == 500


def test_list_artifacts_nonexistent_project(client):
    response = client.get('/artifacts?project_id=1000&run_id=79eac25d801f41f0baa68d322679f12')
    response_json = response.json()

    assert response.status_code == 404
    assert 'Project with ID 1000 not found' in response_json.get('message')


# /stat
# curl -X GET "http://localhost:8080/stat" -H "accept: application/json"

def test_stat_no_running_projects(client):
    response = client.get('/stat')
    response_json = response.json()

    assert response.status_code == 200
    assert len(response_json.get('projects')) == 0


def test_stat_with_running_project(client):
    client.put('/projects/1/run')

    response = client.get('/stat')
    response_json = response.json()

    assert response.status_code == 200
    assert len(response_json.get('projects')) == 1


