#!/usr/bin/env bash
# Run tests in docker
KEYS=$1

docker run -v $(pwd):/home/deploy \
           -v $(pwd)/../../common:/home/common \
           -e WORKSPACE=/home/workspace \
           mlpanel-deploy /bin/bash -c "pytest $KEYS tests/"