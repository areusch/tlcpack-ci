import argparse
import logging
import json
import pathlib
import subprocess

import yaml


_LOG = logging.getLogger()


def write_ansible_inventory(terraform_output, args):
    jenkins_head_node_fqdn = terraform_output["jenkins_head_node_fqdn"]["value"]

    executors = {}
    for key, value in terraform_output.items():
      if key.endswith("_executor_fqdn"):
        for v in value["value"]:
          executors[v] = {}

    inventory = {
      "all": {
        "hosts": {
          jenkins_head_node_fqdn: {},
        },
        "vars": {
          "ansible_ssh_common_args": "-o StrictHostKeyChecking=no",
          "ansible_python_interpreter": "auto",
          "executor_ssh_public_key": str(args.executor_ssh_public_key.resolve()),
          "jenkins_master_container_tag": args.jenkins_master_container_tag,
          "jenkins_homedir_tar_gz": str(args.jenkins_homedir_tar_gz.resolve()),
        },
        "children": {
          "jenkins-head-node": {
            "hosts": {jenkins_head_node_fqdn: {}},
          },
          "executors": {"hosts": executors},
        },
      },
    }
    with open(args.ansible_inventory_path, "w") as inventory_f:
      inventory_f.write(yaml.dump(inventory))



def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--executor-ssh-public-key", required=True, type=pathlib.Path,
                        help="Public key to use when connecting to executors")
    parser.add_argument("--jenkins-master-container-tag", required=True,
                        help="Jenkins container to use")
    parser.add_argument("--jenkins-homedir-tar-gz", required=True, type=pathlib.Path,
                        help="Path to the Jenkins homedir .tar.gz created by configure_jenkins.")
    parser.add_argument("--terraform-output-json", required=True, type=pathlib.Path,
                        help="Path to the Terraform output, formatted as JSON.")
    parser.add_argument("--ansible-inventory-path", required=True, type=pathlib.Path,
                        help="Path to the Ansible inventory file to write.")

    return parser.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(level="INFO")

    with open(args.terraform_output_json) as json_f:
        terraform_output = json.load(json_f)

    write_ansible_inventory(terraform_output, args)

    _LOG.info("Jenkins Head Node FQDN: %s", terraform_output["jenkins_head_node_fqdn"])


if __name__ == "__main__":
    main()
