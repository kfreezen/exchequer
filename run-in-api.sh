#!/bin/bash

API_CONTAINER=$(docker compose ps | grep exchequer-api-api | awk '{print $1}' | head -n1)

if [ -z "$API_CONTAINER" ]; then
    echo "Can't find API container"
    exit 0
fi

docker exec $API_CONTAINER "$@"
