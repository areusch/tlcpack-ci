#!/bin/bash -e

SCRIPTS_DIR=$(dirname "${BASH_SOURCE[0]}")

function get_repo_root() {
    cd "${SCRIPTS_DIR}" && git rev-parse --show-toplevel
}

# Standard paths used in the build infrastructure.

BUILD_DIR="$(get_repo_root)/build"
ARTIFACT_DIR="${BUILD_DIR}/artifact"

JENKINS_CONTAINER_TAG_PATH="${ARTIFACT_DIR}/container-tag.txt"

TERRAFORM_CONFIG_VARS_PATH="${ARTIFACT_DIR}/terraform-vars.txt"
TERRAFORM_BACKEND_CONFIG_PATH="${ARTIFACT_DIR}/terraform-backend-config.txt"
TERRAFORM_PROVIDER_CONFIG_PATH="${ARTIFACT_DIR}/terraform-provider-config.txt"
TERRAFORM_PLAN_PATH="${ARTIFACT_DIR}/terraform-plan.txt"
