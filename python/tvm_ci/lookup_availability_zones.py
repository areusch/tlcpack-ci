import argparse
import json
import logging
import pathlib
import sys

from . import utils

import yaml


_LOG = logging.getLogger(__name__)


def parse_args():
  parser = argparse.ArgumentParser()
  utils.add_tvm_ci_config_arg(parser)
  parser.add_argument("--instance-type", help="Name of the instance type")

  return parser.parse_args()


def main():
  args = parse_args()
  subnet_ids_by_availability_zone = json.load(sys.stdin)

  logging.basicConfig(level="INFO")
  tvm_ci_config = utils.parse_tvm_ci_config(args)

  client = utils.create_boto3_client(tvm_ci_config, "ec2")
  request = dict(
    Filters=[
      {"Name": "instance-type", "Values": [args.instance_type]},
      {"Name": "location", "Values": list(subnet_ids_by_availability_zone)}],
    LocationType="availability-zone")

  _LOG.info("Request: %r", request)
  reply = client.describe_instance_type_offerings(**request)

  _LOG.info("Got reply: %r", reply)

  if len(reply["InstanceTypeOfferings"]) == 0:
    _LOG.error("No offerings found!")
    sys.exit(2)

  json.dump({"id": subnet_ids_by_availability_zone[reply["InstanceTypeOfferings"][0]["Location"]]},
            sys.stdout)
  sys.stdout.write("\n")


if __name__ == "__main__":
  main()
