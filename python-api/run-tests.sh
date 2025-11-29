#!/bin/bash

poetry run coverage run -m pytest -x -v .
poetry run coverage report -m
