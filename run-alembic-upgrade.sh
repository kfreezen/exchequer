#!/bin/bash

API_CONTAINER=$(docker compose ps | grep exchequer-api-api | awk '{print $1}' | head -n1)

if [ -z "$API_CONTAINER" ]; then
    echo "Running locally"
    cd exchequer-api
    poetry run alembic upgrade head
    exit 0
fi

echo "Running migrations on container: $API_CONTAINER"
docker exec $API_CONTAINER alembic upgrade head
