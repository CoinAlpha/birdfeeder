import logging
import os
from unittest.mock import patch

import pytest

from birdfeeder.aws.autoscaling import AwsAutoscaling
from birdfeeder.json_helpers import load_json_from_file

log = logging.getLogger(__name__)

private_ip = "172.20.129.153"
public_ip = "1.1.1.1"


# TODO (vladimir): refactor existing manual fixtures to use vcrpy
def describe_auto_scaling_groups_valid_response():
    return load_json_from_file(os.path.join(os.path.dirname(__file__), "fixtures/describe_auto_scaling_group.json"))


class MockEc2Instance:
    def __init__(self):
        self.private_ip_address = private_ip
        self.public_ip_address = public_ip


class MockBotoResource:
    def __init__(self, _: str, **kwargs):  # type: ignore
        pass

    def Instance(self, _: str) -> MockEc2Instance:  # noqa: N802 - bad naming in boto3
        return MockEc2Instance()


@pytest.fixture()
def asg():
    asg = AwsAutoscaling()
    return asg


def test_get_instances_in_asg(asg):
    with patch.object(
        asg.client, "describe_auto_scaling_groups", return_value=describe_auto_scaling_groups_valid_response()
    ):
        all_instances = asg.get_instances_in_asg("ascendex-proxies")
        log.debug(all_instances)


@patch("boto3.resource", MockBotoResource)
def test_get_asg_instances_ip(asg):
    with patch.object(
        asg.client, "describe_auto_scaling_groups", return_value=describe_auto_scaling_groups_valid_response()
    ):
        ips = asg.get_asg_instances_ip("ascendex-proxies")
        log.debug(ips)
        assert ips == [private_ip] * 2  # multiplying to number of instances in dumped response


def test_region_env_var_override(monkeypatch):
    """Test that we can override default region using env var."""
    region = "ap-northeast-1"
    monkeypatch.setenv("AWS_DEFAULT_REGION", region)
    asg = AwsAutoscaling()
    assert asg.client._client_config.region_name == region
