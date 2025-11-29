#!/bin/bash

source .env

HOST=api.exchequer.co
USER=ubuntu
FILES_ONLY=false
DB_ONLY=false

while getopts "fds" flag; do
  case "${flag}" in
    f) FILES_ONLY=true ;;
    d) DB_ONLY=true ;;
    s) HOST=api.exchequer.co ;;
    *) ;;
  esac
done

if [ "$FILES_ONLY" = false ]; then
    # Make sync file and transfer
    ssh -t $USER@$HOST "cd exchequer-api && bash make-sync.sh"
    scp -r $USER@$HOST:~/exchequer-api/sync.tar.gz .
    tar -xzf sync.tar.gz -C .
    rm sync.tar.gz
    docker exec -i postgres psql -U exchequer exchequer < clear-db.sql
    docker exec -i postgres psql -U exchequer exchequer < sync.sql

    bash run-alembic-upgrade.sh
fi

# Sync files
if [ "$DB_ONLY" = false ]; then
  rsync -avz --exclude='projector' -e ssh $USER@$HOST:/opt/exchequer/storage/volumes/exchequer/data/. $VOLUME_DIR/exchequer/data >&2
fi
