#!/bin/bash -e

cd "$(dirname "$0")"
source "./util.sh" || exit 2

cd "$(get_repo_root)"

crane/run.sh stage-scripts/2-apply-plan-in-crane.sh "${CONFIG_FILE:-config/dev.yaml}"
