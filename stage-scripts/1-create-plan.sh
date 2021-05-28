#!/bin/bash -e

cd "$(dirname "$0")"
source "./util.sh" || exit 2

cd "$(get_repo_root)"

crane/run.sh stage-scripts/1-create-plan-in-crane.sh "${CONFIG_FILE:-config/dev.yaml}"

# docker push from outside dind, so that credentials are available.
docker push $(cat "${ARTIFACT_DIR}/container-tag.txt")
