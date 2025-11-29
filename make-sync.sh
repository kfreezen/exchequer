#!/bin/bash

docker exec -i postgres pg_dump -U exchequer > sync.sql
tar -czf sync.tar.gz sync.sql
rm sync.sql

