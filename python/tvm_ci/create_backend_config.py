import argparse
import logging
import pathlib
import sys

import boto3
import yaml

from . import utils


_LOG = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser()
    utils.add_tvm_ci_config_arg(parser)
    parser.add_argument(
        "--backend-config",
        help="Path to the Terraform backend configuration file to write")
    parser.add_argument(
        "--container-tag",
        help="Path to the container which should run on the Jenkins master")
    parser.add_argument(
        "--provider-config",
        help="Path to the Terraform provider configuration file to write")
    parser.add_argument(
        "--tf-var-file",
        help="Path to Terraform var-file to write containing variables.tf values")
    return parser.parse_args()


def verify_bucket_exists(tvm_ci_config):
    client = utils.create_boto3_client(tvm_ci_config, "s3")
    for bucket in client.list_buckets()["Buckets"]:
        if bucket["Name"] == tvm_ci_config["cluster"]["terraform_s3_state_bucket_name"]:
            bucket_region = client.get_bucket_location(Bucket=bucket["Name"])["LocationConstraint"]
            if bucket_region != tvm_ci_config["cluster"]["aws_region"]:
                _LOG.error("Bucket region (%s) is TF AWS region (%s), please move it or adjust CI config",
                           bucket_region, tvm_ci_config["cluster"]["aws_region"])
                sys.exit(2)

            _LOG.info("Found bucket: %s", bucket)
            return

    _LOG.error("AWS bucket not found: %s", tvm_ci_config["cluster"]["terraform_s3_state_bucket_name"])
    sys.exit(2)


def write_terraform_config(tvm_ci_config_path, tvm_ci_config : dict, provisioner_id_rsa : str, args : argparse.Namespace):
    with open(args.backend_config, "w") as config_f:
        config_f.write(
            ('bucket="{terraform_s3_state_bucket_name}"\n'
             'shared_credentials_file="{aws_credentials_file}"\n'
             'region="{aws_region}"\n'
             'profile="{aws_profile_name}"\n').format(
                aws_credentials_file=utils.get_aws_credentials_path(),
                **tvm_ci_config["cluster"])
        )

    with open(args.provider_config, "w") as config_f:
        config_f.write(
            ('aws_credentials_file="{aws_credentials_file}"\n'
             'aws_region="{aws_region}"\n'
             'aws_credentials_profile="{aws_profile_name}"\n').format(
                aws_credentials_file=utils.get_aws_credentials_path(),
                **tvm_ci_config["cluster"])
        )

    with open(args.tf_var_file, "w") as config_f:
        config_f.write(
            (f'name_prefix = "{tvm_ci_config["cluster"]["name_prefix"]}"\n'
             f'arm_instances_count = {tvm_ci_config["cluster"]["nodes"]["arm"]["num_nodes"]}\n'
             f'cpu_instances_count = {tvm_ci_config["cluster"]["nodes"]["cpu"]["num_nodes"]}\n'
             f'gpu_instances_count = {tvm_ci_config["cluster"]["nodes"]["gpu"]["num_nodes"]}\n'
             f'provisioner_ssh_pubkey_file = "{provisioner_id_rsa}.pub"\n'
             f'provisioner_ssh_private_key_file = "{provisioner_id_rsa}"\n'
             f'tvm_ci_config_path = "{tvm_ci_config_path.resolve()}"\n'
            ))


def main():
    args = parse_args()
    logging.basicConfig(level='INFO')
    utils.strip_aws_environment_variables()

    tvm_ci_config = utils.parse_tvm_ci_config(args)

    verify_bucket_exists(tvm_ci_config)
    provisioner_id_rsa = utils.get_repo_root() / "build" / "artifact" / "secret" / "provisioner-id_rsa"
    utils.generate_ssh_key(provisioner_id_rsa)
    write_terraform_config(args.tvm_ci_config, tvm_ci_config, provisioner_id_rsa, args)


if __name__ == "__main__":
    main()
