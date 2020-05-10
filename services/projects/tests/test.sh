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
PROJECTS_DB_NAME=projects_db
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
  postgres:12.2

echo "Wait for postgres server..."
docker exec \
       $DB_HOST \
          /bin/bash -c \
            'while ! pg_isready; do sleep 1; done;'

echo "Run tests..."
docker run --network=$NETWORK \
           -v $CURDIR/..:/home/projects \
           -v $CURDIR/../../../common:/home/common \
           -e WORKSPACE=/home/workspace \
           -e ARTIFACT_STORE=mlruns \
           -e TRACKING_SERVER_PORTS=5000-5100 \
           -e PROJECTS_DB_NAME=$PROJECTS_DB_NAME \
           -e POSTGRES_USER=$POSTGRES_USER \
           -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
           -e DB_HOST=$DB_HOST \
           -e DB_PORT=$DB_PORT \
           mlrepa/mlpanel-base-projects:latest \
              /bin/bash -c "pytest $KEYS tests/integration"


docker stop $DB_HOST