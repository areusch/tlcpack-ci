#!/usr/bin/env bash

# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

#
# Start a bash, mount /workspace to be current directory.
#
# Usage: bash.sh <CONTAINER_TYPE> [-i] [--net=host] <CONTAINER_NAME>  <COMMAND>
#
# Usage: docker/bash.sh <CONTAINER_NAME>
#     Starts an interactive session
#
# Usage2: docker/bash.sh [-i] <CONTAINER_NAME> [COMMAND]
#     Execute command in the docker image, default non-interactive
#     With -i, execute interactively.
#

set -ex

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 COMMAND"
    exit 2
fi

DOCKER_IMAGE_NAME=tvm-ci-crane:latest

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

WORKSPACE="$(cd "$(dirname "$0")" && git rev-parse --show-toplevel)"

COMMAND=( "$@" )

echo "Running '${COMMAND[@]}' inside ${DOCKER_IMAGE_NAME}..."

# When running from a git worktree, also mount the original git dir.
EXTRA_MOUNTS=( )
if [ -f "${WORKSPACE}/.git" ]; then
    git_dir="$(cd "${WORKSPACE}" && git rev-parse --git-common-dir)"
    if [ "${git_dir}" != "${WORKSPACE}/.git" ]; then
        EXTRA_MOUNTS=( "${EXTRA_MOUNTS[@]}" -v "${git_dir}:${git_dir}" )
    fi
fi

INTERACTIVE=
if [ -t 0 ]; then
    INTERACTIVE=-it
fi

# By default we cleanup - remove the container once it finish running (--rm)
# and share the PID namespace (--pid=host) so the process inside does not have
# pid 1 and SIGKILL is propagated to the process inside (jenkins can kill it).
#    -v /var/run/docker.sock:/var/run/docker.sock \
docker run --privileged --rm --pid=host \
    --network=$(cat "$(dirname "$0")/../build/crane/network-id.txt") \
    -v "/var/run/docker.sock:/var/run/docker.sock:rw" \
    -v "${WORKSPACE}:${WORKSPACE}" \
    -v ${SCRIPT_DIR}:/docker \
    "${EXTRA_MOUNTS[@]}" \
    -w $(pwd) \
    -e "CI_BUILD_HOME=$(pwd)" \
    -e "CI_BUILD_USER=$(id -u -n)" \
    -e "CI_BUILD_UID=$(id -u)" \
    -e "CI_BUILD_GROUP=$(id -g -n)" \
    -e "CI_BUILD_GID=$(id -g)" \
    -e "CI_IMAGE_NAME=${DOCKER_IMAGE_NAME}" \
    ${INTERACTIVE} \
    ${DOCKER_IMAGE_NAME} \
    bash --login /docker/with_the_same_user \
    "${COMMAND[@]}"
