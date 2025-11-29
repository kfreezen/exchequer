# Onboarding

## Prerequisites

Python 3.11 or greater

Poetry 1.7 or greater
Please follow docs here (<https://python-poetry.org/docs/>) to install

Docker Desktop

pandoc needs to be installed for contract generation.
You can install via `brew`

```
brew install pandoc
```

## Use MacOS and pyenv?

Don't have pyenv? You should!
```
brew install pyenv
```
Install a nice version using something like the below.
```
pyenv install 3.11.1
pyenv local 3.11.1
```
Then if you don't have poetry, get it!
```
pip install poetry
```

## Setting Up the API on Your Development Environment

Clone the this Git Repository

Then run the following commands:

### Initialize Development Environment
Run the following command to initialize the development environment, which creates the volumes directory and .env files:
``` cmd
bash init-dev.sh
```
Update any necessary variables in the .env files. If you need credentials, contact someone on the Cleffy team.


### Start Dev Containers
```
bash run.sh
```

### Sync with prod
```
bash sync.sh
```

### Install Python Packages
``` cmd
cd python-api
poetry install
```

### Make sure DB is up to date
``` cmd
poetry run alembic upgrade head
```

### Start FastAPI Server
``` cmd
bash dev.sh
```

# End of Onboarding

## Start Admin Frontend
Open a new terminal in root dir and run the following commands

``` cmd
cd admin-frontend
npm install
npm run dev
```

## Exchequer API

This should be a fairly straightforward deployment setup.

Just run create-storage.sh, or restore a backup of the folder.

Then set your VOLUMES_DIR to point to the storage folder, wherever you want it to go.

Then run

``` cmd
bash run-dev.sh
```

## Development

``` cmd
./init-dev.sh
```

Then, in two terminals separate terminals, run the following commands

``` cmd
cd python-api; ./dev.sh
cd admin-frontend; npm run dev
```

## Development without using Docker Compose

You can also work around using docker compose by spinning up PostgreSQL on your local machine

## Typesense worker refresh

``` cmd
cd python-api
poetry run dump-elastic
```

## Backups

To enable automatic AWS backups, do the following:
* Create an AWS credential profile called `s3-upload` with `aws configure --profile s3-upload`
* Set your default region as `us-west-1` for that profile.
* Create a crontab pointing to the aws-backup.sh script.

## Alembic | Database migrations

``` cmd
poetry shell
```

* Generate migration
``` cmd
alembic revision --autogenerate -m "message"
```

* Apply new migrations to db
Make sure migrations are correct before you run them
``` cmd
alembic upgrade head
```

## Host server setup

Install docker-rollout from https://github.com/wowu/docker-rollout on your host server.

