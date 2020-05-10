#!/usr/bin/env sh
# Run tests in docker

realpath() {
  OURPWD=$PWD
  cd "$(dirname "$1")"
  LINK=$(readlink "$(basename "$1")")
  while [ "$LINK" ]; do
    cd "$(dirname "$LINK")"
    LINK=$(readlink "$(basename "$1")")
  done
  REALPATH="$PWD/$(basename "$1")"
  cd "$OURPWD"
  echo "$REALPATH"
}

KEYS=$1
CURDIR=$(dirname $(realpath "$0"))
NETWORK=mlpanel-test-projects-network
DEPLOY_DB_NAME=deploy_db
POSTGRES_USER=user
POSTGRES_PASSWORD=passw
DB_HOST=mlpanel-database-test
DB_PORT=5432

docker network rm $NETWORK
docker network create -d bridge --internal $NETWORK

echo "Up PostgreSQL..."
docker run \
  -d \
  --network=$NETWORK \
  --name=$DB_HOST \
  -e POSTGRES_PASSWORD=passw \
  -e POSTGRES_USER=user \
  -e PGDATA=/var/lib/postgresql/data/pgdata \
  --rm \
  --expose $DB_PORT \
  postgres

echo "Wait for postgres server..."
docker exec \
       $DB_HOST \
          /bin/bash -c \
            'while ! pg_isready; do sleep 1; done;'

echo "Run tests..."
docker run --network=$NETWORK \
           -v $CURDIR/..:/home/deploy \
           -v $CURDIR/../../../common:/home/common \
           -e WORKSPACE=/home/workspace \
           -e DEPLOY_DB_NAME=$DEPLOY_DB_NAME \
           -e POSTGRES_USER=$POSTGRES_USER \
           -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
           -e DB_HOST=$DB_HOST \
           -e DB_PORT=$DB_PORT \
           mlrepa/mlpanel-base-deploy:latest /bin/bash -c "pytest $KEYS tests/"

docker stop $DB_HOST