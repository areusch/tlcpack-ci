#!/bin/bash -ex

set -xe

cd "$(dirname "$0")"
source "./util.sh" || exit 2

cd "$(get_repo_root)"

eval $(ssh-agent)

ssh-add "${ARTIFACT_DIR}/secret/provisioner-id_rsa"

poetry run python -m tvm_ci.configure_ansible \
       --executor-ssh-public-key=${ARTIFACT_DIR}/executor-ssh-key.pub \
       "--jenkins-master-container-tag=$(cat "${JENKINS_CONTAINER_TAG_PATH}")" \
       "--terraform-output-json=${ARTIFACT_DIR}/terraform-output.json" \
       --jenkins-homedir-tar-gz=${BUILD_DIR}/jenkins-homedir.tar.gz \
       --ansible-inventory-path=${BUILD_DIR}/ansible-inventory.yml

cd ansible
ansible-playbook -i ${BUILD_DIR}/ansible-inventory.yml playbook.yml
