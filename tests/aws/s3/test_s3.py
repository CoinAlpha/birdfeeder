import os
from typing import Any, Dict
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError

from birdfeeder.aws.exceptions import BucketUnavailable, MaxKeyUnavailable
from birdfeeder.aws.s3 import AwsS3
from birdfeeder.json_helpers import load_json_from_file


@pytest.fixture()
def s3():
    s3 = AwsS3(access_key="xxx", secret_key="xxx")
    return s3


def list_objects_v2_response_nonexistent_prefix():
    return load_json_from_file(os.path.join(os.path.dirname(__file__), "fixtures/nonexistent_prefix.json"))


def list_objects_v2_response_valid_response():
    return load_json_from_file(os.path.join(os.path.dirname(__file__), "fixtures/valid_objects_list.json"))


def head_object_response():
    return load_json_from_file(os.path.join(os.path.dirname(__file__), "fixtures/head_object.json"))


def test_init_with_missing_argument_1():
    with pytest.raises(ValueError, match="You must specify both"):
        AwsS3(access_key="test")


def test_init_with_missing_argument_2():
    with pytest.raises(ValueError, match="You must specify both"):
        AwsS3(secret_key="test")


def test_get_max_key_nonexistent_prefix(s3: AwsS3) -> None:
    with patch.object(s3, "_get_page_iterator", return_value=list_objects_v2_response_nonexistent_prefix()):
        with pytest.raises(MaxKeyUnavailable, match="Requested prefix does not exists"):
            s3.get_max_key("hummingbot-mysql-archive", prefix="nonexistent", check_bucket=False)


def test_get_max_key_valid_prefix(s3: AwsS3) -> None:
    with patch.object(s3, "_get_page_iterator", return_value=list_objects_v2_response_valid_response()):
        key = s3.get_max_key("hummingbot-mysql-archive", prefix="parrot/Production", check_bucket=False)

    assert key == "parrot/Production/BinanceUserOrderModel/2020-03-12T00:00:00+00:00__2020-03-13T00:00:00+00:00.sqlite"


def test_get_max_key_nonexistent_bucket(s3: AwsS3) -> None:
    with patch.object(s3, "is_bucket_exists", return_value=False):
        with pytest.raises(BucketUnavailable, match="Bucket does not exists"):
            s3.get_max_key("nonexistent")


def test_is_bucket_exists_good(s3: AwsS3) -> None:
    with patch.object(s3.client, "head_bucket"):
        result = s3.is_bucket_exists("exists")
        assert result is True


def test_is_bucket_exists_bad(s3: AwsS3) -> None:
    with patch.object(
        s3.client, "head_bucket", side_effect=ClientError({"Error": {"Code": "AccessDenied"}}, "head_bucket")
    ):
        result = s3.is_bucket_exists("nonexistent")
        assert result is False


def test_generate_presigned(s3: AwsS3) -> None:
    result = s3.generate_presigned("hummingbot-miner", "test")
    assert "url" in result
    assert "fields" in result


def test_download_with_progressbar(s3: AwsS3) -> None:
    """Test for correct run of download_with_progressbar()"""
    mock_response: Dict[str, Any] = head_object_response()
    total_length: int = mock_response["ContentLength"]

    def mock_download_file(*_, Callback=None):  # noqa: N803
        for downloaded_bytes in range(0, total_length, total_length // 10):
            Callback(downloaded_bytes)

    s3.client.download_file = mock_download_file
    with patch.object(s3.client, "head_object", return_value=mock_response):
        s3.download_with_progressbar("some-bucket", "some-key", "path/to/file")
