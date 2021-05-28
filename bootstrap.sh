#!/bin/bash -e
#
# This script is the bootstrap script that enables local development using this repository.
# Run this script to generate a Makefile that can be used to launch the TVM CI in development mode.

if [ "${BASH_SOURCE[0]}" != "$0" ]; then
    echo "NOTE: don't source bootstrap.sh script; run it like ./${BASH_SOURCE[0]}"
    exit 2
fi

cd "$(dirname $0)"

if [ "$(which docker)" == "" ]; then
    echo "ERROR: docker not found. Please install docker: https://www.docker.com/get-started"
    exit 2
fi

# Build the crane docker image, if needed.
cd crane && make crane
