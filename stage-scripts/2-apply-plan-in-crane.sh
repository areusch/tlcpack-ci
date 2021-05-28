#!/bin/bash -ex

set -xe

cd "$(dirname "$0")"
source "./util.sh" || exit 2

cd "$(get_repo_root)"

CONFIG_FILE="${1}"

rm -rf build/jenkins-homedir
poetry run python -m tvm_ci.jenkins_builder.configure_jenkins \
       --base-casc-config=config/base-jenkins.yaml \
       "--tvm-ci-config=${CONFIG_FILE}" \
       --github-personal-access-token=config/secrets/github-personal-access-token \
       "--jenkins-container=$(cat "${JENKINS_CONTAINER_TAG_PATH}")" \
       --jenkins-container-network-id=$(cat "${BUILD_DIR}/crane/network-id.txt") \
       --jenkins-executor-private-key=${BUILD_DIR}/executor-ssh-key \
       --jenkins-executor-public-key=${ARTIFACT_DIR}/executor-ssh-key.pub \
       --jenkins-homedir=${BUILD_DIR}/jenkins-homedir \
       --jenkins-homedir-tar-gz=${BUILD_DIR}/jenkins-homedir.tar.gz \
       --jenkins-jobs-config-ini=config/jenkins-jobs/jenkins_jobs.ini \
       --jenkins-jobs-files=config/jenkins-jobs

cd infra

terraform apply "${TERRAFORM_PLAN_PATH}"
terraform output -json >"${ARTIFACT_DIR}/terraform-output.json"
