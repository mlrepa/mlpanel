#!/usr/bin/env bash

source functions.sh
handle_help start
check_input_edition

if [ 'base' == $EDITION ]; then
  export $(cat config/base/.env | grep "^[^#;]")
  docker-compose -f config/base/docker-compose.yaml up
else
  echo "Edition $EDITION undefined"
fi;

