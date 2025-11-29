#!/bin/sh
docker network create exchequer 2>/dev/null || true
sh ./create-storage.sh
sh ./create-jwt-key.sh
