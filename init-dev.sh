#!/bin/sh
cp .env.example .env
cp python-api/.env.example python-api/.env
docker network create exchequer 2>/dev/null || true
sh ./create-storage.sh
sh ./create-jwt-key.sh


