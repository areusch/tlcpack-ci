#!/bin/bash -e

function rm_network() {
    if [ -e "$2" ]; then
        network_id=$(docker network ls --format "{{.ID}}")
        if [ -n "${network_id}" ]; then
            docker network rm "${network_id}"
        fi
        rm "$2"
    fi
}

case "$1" in
    create)
        rm_network "$2"
        docker network create tvm-ci-crane >"$2"
        ;;
    rm)
        rm_network "$2"
        ;;
    *)
        echo "$1: unrecognized command"
        exit 2
        ;;
esac
