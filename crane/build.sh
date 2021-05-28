#!/bin/bash -xe


cd "$(dirname "$0")"
docker build -t crane:latest .
