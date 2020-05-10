#!/usr/bin/env bash

source functions.sh
handle_help restart
check_input_edition

if [ 'base' == $EDITION ]; then
  export $(cat config/base/.env | grep "^[^#;]")
  docker-compose -f config/base/docker-compose.yaml down "${POSITIONAL_ARGS[@]}"
  docker-compose -f config/base/docker-compose.yaml up "${POSITIONAL_ARGS[@]}"
else
  echo "Edition $EDITION undefined"
fi;

