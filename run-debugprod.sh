#!/bin/bash

docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.debugprod.yml up --remove-orphans -d

