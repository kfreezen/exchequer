#!/bin/bash

source .env

BACKUP_DATE=$(date +"%Y%m%d%H%M%S")
VOLUME_DIR=${VOLUME_DIR-./storage/volumes}

# Delete previous backups
rm -rf backups/*

if [ "$1" = "-sql" ]; then
  BACKUP_FOLDER=backup-sql-$BACKUP_DATE
  mkdir $BACKUP_FOLDER >&2
  docker exec -i postgres pg_dump -U exchequer > $BACKUP_FOLDER/postgres.sql
elif [ "$1" = "-full" ]; then
  BACKUP_FOLDER=backup-full-$BACKUP_DATE
  mkdir $BACKUP_FOLDER >&2
  cp .env $BACKUP_FOLDER/.env >&2
  docker exec -i postgres pg_dump -U exchequer > $BACKUP_FOLDER/postgres.sql
  cp -r $VOLUME_DIR/exchequer $BACKUP_FOLDER/exchequer >&2
else
  BACKUP_FOLDER=backup-$BACKUP_DATE
  mkdir $BACKUP_FOLDER >&2
  cp .env $BACKUP_FOLDER/.env >&2
  docker exec -i postgres pg_dump -U exchequer > $BACKUP_FOLDER/postgres.sql
  rsync -a --exclude='projector' $VOLUME_DIR/exchequer $BACKUP_FOLDER/exchequer >&2
fi
tar -czf $BACKUP_FOLDER.tar.gz $BACKUP_FOLDER >&2
rm -rf $BACKUP_FOLDER >&2

# If not backups folder, create it
if [ ! -d "backups" ]; then
  mkdir backups
fi

mv "$BACKUP_FOLDER.tar.gz" backups >&2

echo "backups/$BACKUP_FOLDER.tar.gz"
