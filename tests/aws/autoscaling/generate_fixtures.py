#!/usr/bin/env python
import os

import boto3

from birdfeeder.json_helpers import dump_to_file_as_json

path_prefix = "tests/aws/autoscaling/fixtures"


def generate_asg_describe(client):
    autoscaling_group = "ascendex-proxies"
    describe = client.describe_auto_scaling_groups(AutoScalingGroupNames=[autoscaling_group])
    dump_to_file_as_json(describe, os.path.join(path_prefix, "describe_auto_scaling_group.json"))


def main():
    client = boto3.client("autoscaling")
    generate_asg_describe(client)


# Note: not dumping boto3.resource("ec2).Instance here as it's a dynamic object which is not json-serializable

if __name__ == "__main__":
    main()
