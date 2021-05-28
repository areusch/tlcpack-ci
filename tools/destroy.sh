#!/bin/bash -e

cd $(dirname $0)/../infra
terraform destroy \
          -var-file ../build/artifact/terraform-provider-config.txt \
          -var-file ../build/artifact/terraform-vars.txt
