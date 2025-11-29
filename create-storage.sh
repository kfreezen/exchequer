#!/bin/sh
# To run this script on windows use (bash create-strage.sh)
# Because source is a bash builtin command and not available in sh
source .env

mkdir -p $VOLUME_DIR/postgres/data
mkdir -p $VOLUME_DIR/exchequer/data
mkdir -p $VOLUME_DIR/exchequer/config
