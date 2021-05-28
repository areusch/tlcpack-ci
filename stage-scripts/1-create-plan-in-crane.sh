#!/bin/bash -e

cd "$(dirname "$0")"
source "./util.sh" || exit 2

cd "$(get_repo_root)"

CONFIG_FILE="$1"

# poetry run python -m tvm_ci.jenkins_builder.build_container \
#        "--tvm-ci-config=${CONFIG_FILE}" \
#        --required-plugins=config/plugins.txt \
#        "--installed-plugins=${ARTIFACT_DIR}/installed-plugins.txt" \
#        "--container-filename=${ARTIFACT_DIR}/container-tag.txt"

poetry run python -m tvm_ci.create_backend_config \
       "--tvm-ci-config=${CONFIG_FILE}" \
       "--backend-config=${TERRAFORM_BACKEND_CONFIG_PATH}" \
       "--provider-config=${TERRAFORM_PROVIDER_CONFIG_PATH}" \
       "--tf-var-file=${TERRAFORM_CONFIG_VARS_PATH}" \
       "--container-tag=$(cat "${JENKINS_CONTAINER_TAG_PATH}")"

cd infra
terraform init "-backend-config=${TERRAFORM_BACKEND_CONFIG_PATH}"
terraform plan \
          "-var-file=${TERRAFORM_PROVIDER_CONFIG_PATH}" \
          "-var-file=${TERRAFORM_CONFIG_VARS_PATH}" \
          "-out=${TERRAFORM_PLAN_PATH}"
