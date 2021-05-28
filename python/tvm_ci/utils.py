import argparse
import collections
import configparser
import logging
import os
import pathlib
import subprocess
import sys

import boto3
import yaml


_LOG = logging.getLogger(__name__)


REPO_ROOT = None


def get_repo_root() -> pathlib.Path:
    global REPO_ROOT
    if REPO_ROOT is None:
        REPO_ROOT = pathlib.Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"],
                                                         encoding="utf-8").rstrip("\n"))
    return REPO_ROOT


def get_aws_config_path() -> pathlib.Path:
    return get_repo_root() / "config" / "aws-config"


def get_aws_credentials_path() -> pathlib.Path:
    return get_repo_root() / "config" / "secrets" / "aws-credentials"


def strip_aws_environment_variables():
    """Remove any AWS_ environment variables."""
    env_keys = list(os.environ.keys())
    did_unset_env = False
    for k in env_keys:
        if k.startswith("AWS_"):
            _LOG.info("Deleting environment variable %s", k)
            os.unsetenv(k)
            did_unset_env = True

    if did_unset_env:
        _LOG.warning("Some AWS_ environment variables were ignored by this proces.")
        _LOG.warning("aws plugins should be configured only through config files.")

    for env_var, path in (("AWS_SHARED_CREDNETIALS_FILE", get_aws_credentials_path()),
                          ("AWS_CONFIG_FILE", get_aws_config_path())):
        if not path.exists():
            _LOG.error("Cannot force-set environment var %s: file not found: %s", env_var, path)
            sys.exit(2)

        os.putenv(env_var, path)


# Contains the credential kwargs to boto3.Client()
Credentials = collections.namedtuple("Credentials", ["aws_access_key_id", "aws_secret_access_key"])


def parse_aws_credentials(profile_name: str="default") -> Credentials:
    config = configparser.ConfigParser()
    config.read(get_aws_credentials_path())
    return Credentials(**config[profile_name])


def create_boto3_client(tvm_ci_config, service_name):
    aws_profile_name = tvm_ci_config["cluster"].get('aws_profile_name', 'default')
    credentials = parse_aws_credentials(aws_profile_name)
    # NOTE: region from force-overridden AWS_CONFIG_FILE environment var.
    return boto3.client(service_name, **credentials._asdict(),
                        region_name=tvm_ci_config["cluster"]["aws_region"])


def add_tvm_ci_config_arg(parser : argparse.ArgumentParser):
    """Add --config argument to ArgumentParser."""
    parser.add_argument("--tvm-ci-config", type=pathlib.Path, required=True,
                        help="Path to a yaml file in config/ which describes high-level CI config")


def parse_tvm_ci_config(args : argparse.Namespace):
    with open(args.tvm_ci_config) as ci_config_f:
        return yaml.safe_load(ci_config_f)


def generate_ssh_key(private_key_path, public_key_path=None):
    private_key_path.parent.mkdir(parents=True, exist_ok=True)
    private_key_path.unlink(missing_ok=True)
    subprocess.check_call(["ssh-keygen", "-t", "rsa", "-b", "2048", "-N", "", "-f",
                           str(private_key_path)])
    if public_key_path is not None:
        pathlib.Path(str(private_key_path) + ".pub").rename(public_key_path)
