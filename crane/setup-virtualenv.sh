#!/bin/bash -ex

set -ex

cd "$(dirname "$0")"
cd "$(git rev-parse --show-toplevel)"

mkdir -p "$(pwd)/build/crane"
poetry config --local virtualenvs.path "$(pwd)/build/crane/venv"
poetry lock
poetry install
