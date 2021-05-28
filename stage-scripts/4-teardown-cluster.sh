#!/bin/bash -e

cd "$(dirname "$0")"
source "./util.sh" || exit 2

cd "$(get_repo_root)"

cd infra
terraform destroy \
          -var-file ../build/artifact/terraform-provider-config.txt \
          -var-file ../build/artifact/terraform-vars.txt
