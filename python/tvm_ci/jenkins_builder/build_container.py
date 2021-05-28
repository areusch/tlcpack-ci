import argparse
import logging
import re
import pathlib
import shutil
import subprocess

import requests

from .. import utils
from . import jenkins_lib


_LOG = logging.getLogger(__name__)


VERSION_RE = re.compile(r"^v(?P<major>[0-9]+)\.(?P<minor>[0-9]+)([^0-9].*)?$")


def _determine_publish_version(container_name):
    reply = requests.get(f"https://registry.hub.docker.com/v1/repositories/{container_name}/tags")
    reply.raise_for_status()

    versions = []
    for layer in reply.json():
        m = VERSION_RE.match(layer["name"])
        if not m:
            _LOG.warn("Not considering tag for %s with unexpected format: %s",
                      container_name, layer["name"])
            continue

        versions.append((int(m.group("major")), int(m.group("minor"))))

    versions.sort()
    if not versions:
        versions.append((0, 0))

    last = versions[-1]
    return f"v{last[0]}.{last[1] + 1}"


def build(args : argparse.Namespace, container_tag) -> list:
    jenkins_builder = utils.get_repo_root() / "jenkins-builder"
    build_dir = jenkins_builder / "build"
    if not build_dir.exists():
        build_dir.mkdir(parents=True)
    shutil.copy2(args.required_plugins, build_dir / "required-plugins.txt")
    shutil.copy2(utils.get_repo_root() / "config" / "Dockerfile",
                 jenkins_builder / "Dockerfile")
    docker_args = ["docker", "build", "--no-cache", "-t", container_tag, "."]

    proc = subprocess.Popen(docker_args, cwd=jenkins_builder,
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            encoding="UTF-8")
    is_capturing_to_plugins = False
    did_finish_capturing_to_plugins = False
    installed_plugins = []
    for line in proc.stdout:
        if line[-1] == "\n":
            line = line[:-1]
        _LOG.info("docker build: %s", line)
        if (not is_capturing_to_plugins and
            not did_finish_capturing_to_plugins and
            line.endswith("Installed plugins:")):
            _LOG.info("--> capturing")
            is_capturing_to_plugins = True
            continue
        elif is_capturing_to_plugins and not did_finish_capturing_to_plugins and ":" not in line:
            _LOG.info("<-- captured")
            did_finish_capturing_to_plugins = True
        elif is_capturing_to_plugins and not did_finish_capturing_to_plugins:
            installed_plugins.append(line)

    proc.wait()
    assert proc.returncode == 0, f"command exited with code {proc.returncode}: {' '.join(docker_args)}"

    return installed_plugins


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a Jenkins container with the plugins installed")
    utils.add_tvm_ci_config_arg(parser)
    parser.add_argument("--container-filename",
                        type=pathlib.Path,
                        help=("When supplied and --publish-to is supplied, write the name:tag of the "
                              "published docker container to this file."))
    parser.add_argument("--installed-plugins", required=True,
                        type=pathlib.Path,
                        help=("Path to a file which will be filled with a list of the installed "
                              "plugins and their versions. This list includes dependencies of the "
                              "plugins listed in --required-plugins."))
    parser.add_argument("--required-plugins", required=True,
                        help=("Path to a text file listing the required plugins to be installed. "
                              "Should be readable by install-plugins.sh in jenkins/jenkins:lts"))
    return parser.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(level="INFO")

    tvm_ci_config = utils.parse_tvm_ci_config(args)
    container_name = tvm_ci_config['docker']['jenkins_container_name']

    publish_version = _determine_publish_version(container_name)
    container_tag = f"{container_name}:{publish_version}"
    _LOG.info("Will tag as %s", container_tag)

    installed_plugins = build(args, publish_version)

    args.installed_plugins.parent.mkdir(parents=True, exist_ok=True)
    with open(args.installed_plugins, "w") as installed_f:
        for plugin in installed_plugins:
            installed_f.write(plugin)
            installed_f.write("\n")

    _LOG.info("Tagging and publishing...")
    subprocess.check_output(["docker", "tag", "tvm_ci.jenkins:latest", container_tag])

    if args.container_filename:
        args.container_filename.parent.mkdir(parents=True, exist_ok=True)
        with open(args.container_filename, "w") as container_f:
            container_f.write(container_tag)


if __name__ == "__main__":
    main()
