"""
This script generates demo workspace.

"""

from dotenv import dotenv_values
from http import HTTPStatus
import logging
import os
import requests
import subprocess as sp
import time


logging.basicConfig(level=logging.DEBUG)

URI = 'http://0.0.0.0:8089'
ENVS = dotenv_values('../../../config/base/.env')
GOOGLE_APPLICATION_CREDENTIALS = ENVS.get('GOOGLE_APPLICATION_CREDENTIALS', '/').split('/')[-1]
GOOGLE_APPLICATION_CREDENTIALS = f'../../../config/credentials/{GOOGLE_APPLICATION_CREDENTIALS}'


def generate_project(name):

    logging.info(f'Creating project "{name}"')
    create_resp = requests.post(url=f'{URI}/projects', data={'name': name}, verify=False).json()
    print(create_resp)
    project_id = create_resp.get('id')
    tracking_uri = create_resp.get('mlflowUri')
    
    logging.info(f'Run tracking server of project "{name}"')
    requests.put(url=f'{URI}/projects/{project_id}/run', verify=False)
    project_healthcheck_resp = requests.get(url=f'{URI}/projects/{project_id}/healthcheck', verify=False)

    if project_healthcheck_resp.status_code == 200:

        print()
        logging.info('Wait until tracking server run...')
        waiting_time = 20
        tracking_server_loaded = False

        while True:
            print(str(waiting_time) + ' seconds...')
            try:
                r = requests.get(tracking_uri, verify=False)

                if r.status_code == HTTPStatus.OK:
                    tracking_server_loaded = True
                    break

            except requests.ConnectionError:
                pass

            time.sleep(1)
            waiting_time -= 1

            if waiting_time <= 0:
                break
        if tracking_server_loaded:

            print()
            logging.info('Run examples...')
            logging.info('run example1.py ...')
            p1 = sp.Popen(
                f'export MLFLOW_TRACKING_URI={tracking_uri} && '
                f'export MLFLOW_TRACKING_INSECURE_TLS="true" && '
                f'python example1.py',
                shell=True
            )
            p1.wait()

            print()
            logging.info('run example2.py with default parameters...')
            p2 = sp.Popen(
                f'export MLFLOW_TRACKING_URI={tracking_uri} && '
                f'export MLFLOW_TRACKING_INSECURE_TLS="true" && '
                f'export GOOGLE_APPLICATION_CREDENTIALS={GOOGLE_APPLICATION_CREDENTIALS} && '
                f'python example2.py',
                shell=True
            )
            p2.wait()

            print()
            logging.info('run example2.py with cli parameters...')
            p3 = sp.Popen(
                f'export MLFLOW_TRACKING_URI={tracking_uri} && '
                f'export MLFLOW_TRACKING_INSECURE_TLS="true" && '
                f'export GOOGLE_APPLICATION_CREDENTIALS={GOOGLE_APPLICATION_CREDENTIALS} && '
                f'python example2.py --C 0.1 --solver newton-cg',
                shell=True
            )
            p3.wait()

            print()
            logging.info('run example3.py with default parameters...')
            p4 = sp.Popen(
                f'export MLFLOW_TRACKING_URI={tracking_uri} && '
                f'export MLFLOW_TRACKING_INSECURE_TLS="true" && '
                f'export GOOGLE_APPLICATION_CREDENTIALS={GOOGLE_APPLICATION_CREDENTIALS} && '
                f'python example3.py',
                shell=True
            )
            p4.wait()

            print()
            logging.info('run example3.py with cli parameters...')
            p5 = sp.Popen(
                f'export MLFLOW_TRACKING_URI={tracking_uri} && '
                f'export MLFLOW_TRACKING_INSECURE_TLS="true" && '
                f'export GOOGLE_APPLICATION_CREDENTIALS={GOOGLE_APPLICATION_CREDENTIALS} && '
                f'python example3.py --C 0.1 --kernel linear',
                shell=True
            )
            p5.wait()

            print()
            logging.info('Terminate tracking server')

            requests.put(url=f'{URI}/projects/{project_id}/terminate', verify=False)

        else:

            print()
            logging.error('Tracking server did not run in 20 seconds!')

    else:

        print()
        logging.error(f'Project "{name}" did not run!')


if __name__ == '__main__':

    logging.info('check FastAPI app is running...')
    healthcheck_resp = None

    try:
        healthcheck_resp = requests.get(f'{URI}/healthcheck', verify=False)
    except requests.ConnectionError:
        pass

    if healthcheck_resp is not None:

        print()
        logging.info('FastAPI app is running! Continue...')

        generate_project('Demo')
        generate_project('Demo2')

    else:

        print()
        logging.error('FastAPI app is not running!')
