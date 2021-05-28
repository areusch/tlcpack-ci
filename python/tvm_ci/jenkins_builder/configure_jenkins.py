import argparse
import atexit
import contextlib
import logging
import pathlib
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import threading
import time

import requests
import yaml

from .. import utils
from . import jenkins_lib


_LOG = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Build Jenkins homedir for a particular Jenkins config")
    utils.add_tvm_ci_config_arg(parser)
    parser.add_argument("--base-casc-config", type=pathlib.Path,
                        help="Path to the Configuration-as-Code yaml config.")
    parser.add_argument("--enable-prod-auth",
                        action="store_true",
                        help=("Enable prod authentication strategy. When not specified, builds an "
                              "unsecured Jenkins head node."))
    parser.add_argument("--github-personal-access-token",
                        type=pathlib.Path,
                        help=("Path to a file containing a GitHub Personal Accesss Token for the user "
                              "account identifed in the \"review_bot_github_username\" key of the "
                              "--jenkins-jobs-config-ini file."))
    parser.add_argument("--jenkins-executor-private-key",
                        type=pathlib.Path,
                        required=True,
                        help=("Path to a file which will be created using ssh-keygen. This file will "
                              "hold the executor private key."))
    parser.add_argument("--jenkins-executor-public-key",
                        type=pathlib.Path,
                        required=True,
                        help=("Path to a file which will be created using ssh-keygen. This file will "
                              "hold the executor public key."))

    jenkins_lib.add_arguments(parser)

    parser.add_argument("--jenkins-jobs-config-ini", help="Path to config.ini for jenkins_jobs module")
    parser.add_argument("--jenkins-homedir-tar-gz",
                        help="Path to a tar archive which will be created containing the Jenkins homedir")
    parser.add_argument("--jenkins-jobs-files", action='append', default=[],
                        help="Job configuration file to load. May be repeated.")
    parser.add_argument("--jenkins-container-network-id", required=True,
                        help="Docker network to place Jenkins container on")
    parser.add_argument("--log-level", default="INFO", help="Log level to use")
    return parser.parse_args()


class UnprotectedCredentialsError(Exception):
    """Raised when credentials are not adequately protected on-disk."""


def generate_ssh_keys(args : argparse.Namespace):
    args.jenkins_executor_private_key.unlink(missing_ok=True)
    pathlib.Path(str(args.jenkins_executor_private_key) + ".pub").unlink(missing_ok=True)
    utils.generate_ssh_key(args.jenkins_executor_private_key, args.jenkins_executor_public_key)
    with open(args.jenkins_executor_private_key) as key_f:
        return key_f.read()


def generate_casc(args : argparse.Namespace, tvm_ci_config : dict, executor_private_key: str) -> dict:
    # Extra environment vars to inject. The return value of this function.
    extra_env = {}

    with open(args.base_casc_config) as base_config_f:
        config = yaml.safe_load(base_config_f.read())

    # Prod auth strategy will be configured later on. Use unsecured here to allow jobs to be
    # configured.
    config["jenkins"]["authorizationStrategy"] = "unsecured"

    password_file = args.github_personal_access_token
    if password_file.exists():
        password_mode = stat.S_IMODE(password_file.stat().st_mode)
        if (password_mode & ~0o600) != 0:
            raise UnprotectedCredentialsError(
                "GH credentials are not well-enough protected "
                f"(mode {password_mode:o}): {password_file}")

        with open(password_file) as password_f:
            extra_env["JENKINS_PASSWORD_GITHUB"] = password_f.read().rstrip("\n")

        config["credentials"] = {
            "system": {
                "domainCredentials": [
                    {
                        "credentials": [
                            {
                                "usernamePassword": {
                                    "id": "github-credential",
                                    "username": tvm_ci_config["jenkins"]["review_bot_github_username"],
                                    "password": "${JENKINS_PASSWORD_GITHUB}",
                                    "description": "Credentials used with the GitHub Branch Source Plugin",
                                    "scope": "GLOBAL",
                                },
                            },
                            {
                                "basicSSHUserPrivateKey": {
                                    "id": "agent-ssh-key",
                                    "privateKeySource": {
                                        "directEntry": {
                                            "privateKey": executor_private_key,
                                        },
                                    },
                                },
                            },
                        ],
                    },
                ],
            },
        }

    else:
        if tvm_ci_config["mode"] == "prod":
            raise NoCredentialsError("No GitHub credentials found and building for prod")
        _LOG.warn("No GitHub credentials found, Jenkins will not poll for changes")

    config["jenkins"]["nodes"] = []
    for node_type, node_config in tvm_ci_config["cluster"]["nodes"].items():
        for i in range(node_config["num_nodes"]):
            node_name = f'{tvm_ci_config["cluster"]["name_prefix"]}jenkins-{node_type}-executor-{i}'
            node_fqdn = f'{node_name}.{tvm_ci_config["cluster"]["dns_suffix"]}'
            config["jenkins"]["nodes"].append({
                "permanent": {
                    "labelString": " ".join(node_config["labels"]),
                    "launcher": {
                        "ssh": {
                            "credentialsId": "agent-ssh-key",
                            "host": node_fqdn,
                            "port": 22,
                            "sshHostKeyVerificationStrategy": "nonVerifyingKeyVerificationStrategy",
                        },
                    },
                    "name": node_name,
                    "nodeDescription": f"Permanent executor {node_type}-{i}",
                    "numExecutors": node_config["num_executors"],
                    "remoteFS": "/home/jenkins",
                    "retentionStrategy": "always",
              }
          })

    jenkins_yaml_path = args.jenkins_homedir / "jenkins.yaml"
    with open(jenkins_yaml_path, "w") as jenkins_yaml_f:
        jenkins_yaml_f.write(yaml.dump(config))

    return extra_env


def configure_jenkins(args : argparse.Namespace, tvm_ci_config : dict, executor_private_key : str) -> dict:
    if args.jenkins_homedir.exists():
        sys.exit(f"--jenkins-homedir: file exists: {args.jenkins_homedir}")

    os.makedirs(args.jenkins_homedir)
    return generate_casc(args, tvm_ci_config, executor_private_key)


def configure_jobs(args : argparse.Namespace):
    config_str = ":".join(args.jenkins_jobs_files)

    subprocess.check_output([sys.executable, "-m", "jenkins_jobs",
                             "--conf", args.jenkins_jobs_config_ini,
                             "update", config_str])


def set_prod_auth_strategy(args : argparse.Namespace, tvm_ci_config : dict):
    jenkins_yaml_path = args.jenkins_homedir / "jenkins.yaml"
    with open(jenkins_yaml_path) as jenkins_yaml_f:
        config = yaml.safe_load(jenkins_yaml_f)

    config["jenkins"]["authorizationStrategy"] = {
        "github": {
            "adminUserNames": ", ".join(cluster["admin_github_usernames"]),
            "organizationNames": "",
            "allowAnonymousJobStatusPermission": True,
            "allowAnonymousReadPermission": True,
            "allowCcTrayPermission": False,
            "allowGithubWebHookPermission": False,
            "authenticatedUserCreateJobPermission": False,
            "authenticatedUserReadPermission": True,
            "useRepositoryPermissions": False,
        },
    }

    with open(jenkins_yaml_path, "w") as jenkins_yaml_f:
        jenkins_yaml_f.write(yaml.dump(config))

#    _LOG.info("updating config-as-code: %r", requests.post("http://localhost:8080/configuration-as-code/reload"))

    sess = requests.Session()
    r = sess.get("http://localhost:8080/crumbIssuer/api/json")  # NOTE: no username/password needed.
    r.raise_for_status()

    r = sess.post("http://localhost:8080/configuration-as-code/reload",
                  headers={"Jenkins-Crumb": r.json()["crumb"]})
    r.raise_for_status()


JENKINS_CONTAINER_NAME = 'tvm-ci-embryonic-jenkins'


def main():
    args = parse_args()
    logging.basicConfig(level=args.log_level)

    executor_private_key = generate_ssh_keys(args)

    tvm_ci_config = utils.parse_tvm_ci_config(args)

    extra_env = configure_jenkins(args, tvm_ci_config, executor_private_key)
    with tempfile.NamedTemporaryFile() as tf:
        for key, val in extra_env.items():
            tf.write(bytes(f"{key}={val}\n", "utf-8"))
        tf.flush()

        extra_docker_opts = ["--env-file", tf.name, "--name", JENKINS_CONTAINER_NAME]
        if args.jenkins_container_network_id:
            extra_docker_opts.extend(["--network", args.jenkins_container_network_id])
        with jenkins_lib.launch_jenkins(args, [], extra_docker_opts=extra_docker_opts) as container_id:
            time.sleep(5)
            configure_jobs(args)
            if args.enable_prod_auth:
                set_prod_auth_strategy(args, tvm_ci_config)

    (args.jenkins_homedir / "jenkins.yaml").unlink()
    with tarfile.open(args.jenkins_homedir_tar_gz, "w:gz") as tf:
        def reset(tarinfo):
            tarinfo.uid = tarinfo.gid = 0
            tarinfo.uname = tarinfo.gname = "root"
            return tarinfo

        tf.add(args.jenkins_homedir, arcname="jenkins-homedir", filter=reset)


if __name__ == "__main__":
    main()
