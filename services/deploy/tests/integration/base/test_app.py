import json
import pytest
import re
import shutil
from starlette.testclient import TestClient
import time

from deploy.src import app, config


@pytest.fixture(scope='module')
def client():

    app.init()

    return TestClient(app.app)


@pytest.fixture(scope='module')
def deployment_run_timeout():

    return 20


def teardown_module():

    shutil.rmtree(config.Config().get('WORKSPACE'), ignore_errors=True)


# Tests on default (just created = empty) database

# # GET /deployments
def test_list_deployments_default(client):

    response = client.get('/deployments')

    assert response.status_code == 200
    assert response.json() == []


# # GET /deployments/{deployment_id}
def test_get_nonexistent_deployment(client):

    response = client.get('/deployments/1')

    assert response.status_code == 404
    assert response.json().get('message') == 'Deployment with ID 1 not found'


# # PUT /deployments/{deployment_id}/run
def test_run_nonexistent_deployment(client):

    response = client.put('/deployments/1/run')

    assert response.status_code == 404
    assert response.json().get('message') == 'Deployment with ID 1 not found'


# # PUT /deployments/{deployment_id}/stop
def test_stop_nonexistent_deployment(client):

    response = client.put('/deployments/1/stop')

    assert response.status_code == 404
    assert response.json().get('message') == 'Deployment with ID 1 not found'


# # DELETE /deployments/{deployment_id}
def test_delete_nonexistent_deployment(client):

    response = client.delete('/deployments/1')

    assert response.status_code == 404
    assert response.json().get('message') == 'Deployment with ID 1 not found'


# Test deployed model

# # POST /deployments
def test_create_deployment(client):

    create_response = client.post(
        '/deployments',
        data={
            'project_id': 1,
            'model_id': 'IrisLogregModel',
            'version': '1',
            'model_uri': './tests/integration/base/model',
            'type': 'local'
        }
    )

    assert create_response.status_code == 202
    assert create_response.json().get('deployment_id') == '1'

    get_response = client.get('/deployments/1')
    deployment = get_response.json()

    assert get_response.status_code == 200
    assert isinstance(deployment, dict)
    assert deployment.get('id') == '1'
    assert deployment.get('status') == 'running'
    assert deployment.get('type') == 'local'
    assert deployment.get('host') == '0.0.0.0'
    assert re.match(r'''^([\s\d]+)$''', deployment.get('port', '')) is not None


def test_predict(client, deployment_run_timeout):

    deployment_is_running = False
    start = time.time()

    while not deployment_is_running:

        ping_resp = client.get('/deployments/1/ping')

        if ping_resp.status_code == 200:
            deployment_is_running = True

        if time.time() - start > deployment_run_timeout:
            break

    predict_resp = client.post(
        '/deployments/1/predict',
        data={
            'data': '{"schema": {"fields":[{"name":"index","type":"integer"},'
                    '{"name":"sepal_length","type":"number"},{"name":"sepal_width","type":"number"},'
                    '{"name":"petal_length","type":"number"},{"name":"petal_width","type":"number"}],'
                    '"primaryKey":["index"],"pandas_version":"0.20.0"}, '
                    '"data": [{"index":0,"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,'
                    '"petal_width":0.2},{"index":1,"sepal_length":4.9,"sepal_width":3.0,"petal_length":1.4,'
                    '"petal_width":0.2},{"index":2,"sepal_length":4.7,"sepal_width":3.2,"petal_length":1.3,'
                    '"petal_width":0.2},{"index":3,"sepal_length":4.6,"sepal_width":3.1,"petal_length":1.5,'
                    '"petal_width":0.2}]}'
        }
    )

    assert predict_resp.status_code == 200
    assert len(json.loads(predict_resp.json()['prediction'])) == 4


# # POST /deployments
def test_create_bad_type_deployment(client):

    create_response = client.post(
        '/deployments',
        data={
            'project_id': 1,
            'model_id': 'IrisLogregModel',
            'version': '1',
            'model_uri': './tests/integration/model_without_schema/model',
            'type': 'unknown'
        }
    )

    assert create_response.status_code == 400
    assert create_response.json().get('message') == 'Invalid deployment type: unknown'


# # PUT /deployments/{deployment_id}/stop
def test_stop_deployment(client):

    stop_response = client.put('/deployments/1/stop')

    assert stop_response.status_code == 200
    assert stop_response.json().get('deployment_id') == '1'

    get_response = client.get('/deployments/1')
    deployment = get_response.json()

    assert get_response.status_code == 200
    assert isinstance(deployment, dict)
    assert deployment.get('id') == '1'
    assert deployment.get('status') == 'stopped'
    assert deployment.get('type') == 'local'
    assert deployment.get('host') is None
    assert deployment.get('port') is None


# # DELETE /deployments/{deployment_id}
def test_delete_deployment(client):

    delete_response = client.delete('/deployments/1')

    assert delete_response.status_code == 200
    assert delete_response.json().get('deployment_id') == '1'

    get_response = client.get('/deployments/1')

    assert get_response.status_code == 404
    assert get_response.json().get('message') == 'Deployment with ID 1 not found'

