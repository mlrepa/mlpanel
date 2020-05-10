#!/usr/bin/env bash

source functions.sh
handle_help build
check_input_edition

if [ 'base' == $EDITION ]; then

  DOCKER_FOLDER="config/base/docker"

  echo "***Base image***"
  docker build -t mlrepa/mlpanel-base:v0.2 $DOCKER_FOLDER/base

  echo "***Deploy image***"
  docker build -t mlrepa/mlpanel-base-deploy:v0.2 $DOCKER_FOLDER/deploy

  echo "***Projects image***"
  docker build -t mlrepa/mlpanel-base-projects:v0.2 $DOCKER_FOLDER/projects

  echo "***UI image***"
  docker build -t mlrepa/mlpanel-base-ui:v0.2 $DOCKER_FOLDER/ui

  echo "***Web image***"
  docker build -t mlrepa/mlpanel-base-web:v0.2 $DOCKER_FOLDER/web

else
  echo "Edition $EDITION undefined"

fi;