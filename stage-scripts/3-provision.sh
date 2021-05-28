#!/bin/bash -e

cd "$(dirname "$0")"
source "./util.sh" || exit 2

cd "$(get_repo_root)"

crane/run.sh stage-scripts/3-provision-in-crane.sh
