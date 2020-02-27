#!/usr/bin/env bash
# Run tests in docker
KEYS=$1

docker run -v $(pwd):/home/projects \
           -v $(pwd)/../../common:/home/common \
           -e WORKSPACE=/home/workspace \
           -e ARTIFACT_STORE=mlruns \
           -e MLFLOW_TRACKING_SERVERS_PORTS_RANGE=5000-5020 \
           mlpanel-projects /bin/bash -c "pytest $KEYS tests/"