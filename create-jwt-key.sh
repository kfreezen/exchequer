#!/bin/sh

source .env

ssh-keygen -t rsa -b 2048 -m PEM -f $VOLUME_DIR/exchequer/config/jwt-key.pem
