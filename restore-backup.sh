#!/bin/bash

source .env

BACKUP_TAR=$1

echo "Untarring $BACKUP_TAR"
tar -xzf $BACKUP_TAR -C .
# Get the base name of tar file and remove .tar.gz
BACKUP_DIR=$(basename $BACKUP_TAR .tar.gz)
echo "Backup directory: $BACKUP_DIR"

ERROR=0
if [[ $BACKUP_DIR == *"sql"* ]]; then
    echo "SQL-only backup detected, skipping exchequer directory check"
elif [ -d $BACKUP_DIR/exchequer ]; then
    rm -rf $VOLUME_DIR/exchequer
    cp -r $BACKUP_DIR/exchequer/exchequer $VOLUME_DIR/
else
    echo "No exchequer directory found in backup"
    ERROR=1
fi

if [ -f $BACKUP_DIR/postgres.sql ]; then
    docker exec -i postgres psql -U exchequer exchequer < clear-db.sql
    docker exec -i postgres psql -U exchequer exchequer < $BACKUP_DIR/postgres.sql
else
    echo "No postgres.sql file found in backup"
    ERROR=1
fi

if [ $ERROR -eq 0 ]; then
    rm -rf $BACKUP_DIR
else
    echo "Restore failed. Keeping $BACKUP_DIR for further investigation."
fi


bash run.sh
bash run-alembic-upgrade.sh

