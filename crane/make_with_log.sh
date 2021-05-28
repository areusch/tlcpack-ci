#!/bin/bash -xe

set -xe -o pipefail

log="$1"
shift

rm -f "${log}" "${log}.wip" "${log}.error"
(("$@" 2>&1 </dev/null | tee "${log}.wip") && mv "${log}.wip" "${log}") || mv "${log}.wip" "${log}.error"
