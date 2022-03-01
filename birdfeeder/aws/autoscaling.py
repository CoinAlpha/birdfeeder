import logging
from typing import Any, Dict, List

import boto3

from birdfeeder.aws.base import AwsBase

log = logging.getLogger(__name__)


class AwsAutoscaling(AwsBase):
    """Helper class to work with Autoscaling Groups."""

    _service = "autoscaling"

    def get_instances_in_asg(self, autoscaling_group: str) -> List[Dict[str, Any]]:
        """
        Returns EC2 instances inside autoscaling group.

        :param autoscaling_group: AWS autoscaling group name
        """
        asg = self.client.describe_auto_scaling_groups(AutoScalingGroupNames=[autoscaling_group])
        instances = asg["AutoScalingGroups"][0]["Instances"]
        return instances

    def get_asg_instances_ip(self, autoscaling_group: str, return_public_ip: bool = False) -> List[str]:
        """
        Return IPs of the instances in the autoscaling group.

        :param autoscaling_group: AWS autoscaling group name
        :param return_public_ip: if True, return public IP of the instances
        """
        instances = self.get_instances_in_asg(autoscaling_group)
        ec2 = boto3.resource("ec2", region_name=self._region_name)
        instances_resource = [ec2.Instance(i["InstanceId"]) for i in instances]
        attr_name = "public_ip_address" if return_public_ip else "private_ip_address"
        return [getattr(i, attr_name) for i in instances_resource]
