#!/bin/bash
FORCE=false

if [ "$1" = "--force" ]; then
  FORCE=true
fi

# The docker files used are specified in .env file (COMPOSE_FILE)
docker compose build

if [ $? -ne 0 ]; then
  echo "Failed to build docker images"
  exit 1
fi

if [ "$FORCE" = true ]; then
  API_CONTAINER=$(docker compose ps | grep exchequer-api-api | awk '{print $1}' | head -n1)
  docker stop ${API_CONTAINER:-api}
  docker rm ${API_CONTAINER:-api}
fi

docker rollout api
docker rollout frontend
docker rollout exchequer-app

docker compose up --remove-orphans -d
