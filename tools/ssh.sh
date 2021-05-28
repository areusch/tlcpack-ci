#!/bin/bash -e

TERRAFORM_OUTPUT_PATH="$(dirname "$0")/../build/artifact/terraform-output.json"

case "$1" in
    "")
        echo "usage: $0 (head | <executor_type>) [index]"
        echo "<executor_type> is one of cpu, gpu, arm"
        exit 2
        ;;
    "head")
        fqdn=$(cat "${TERRAFORM_OUTPUT_PATH}" | jq -r ".jenkins_head_node_fqdn.value")
        ;;
    *)
        if [ "$2" == "" ]; then
            echo "usage: $0 $1 <index>"
            exit 2
        fi
        fqdn=$(cat "${TERRAFORM_OUTPUT_PATH}" | jq -r ".${1}_executor_fqdn.value[$2]")
        echo "A${fqdn}A"
        if [ "${fqdn}" == "" ]; then
            echo "no such output value: ${1}_executor_fqdn.value[$2]"
            exit 2
        fi
        ;;
esac

echo "ssh ubuntu@${fqdn}"
ssh \
    -i $(dirname $0)/../build/artifact/secret/provisioner-id_rsa \
    -o "UserKnownHostsFile=/dev/null" \
    -o "StrictHostKeyChecking=no" \
    -L 8080:localhost:8080 \
    "ubuntu@${fqdn}"
