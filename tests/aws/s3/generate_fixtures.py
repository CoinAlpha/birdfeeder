#!/usr/bin/env python

import os
from typing import Any, List

import boto3

from birdfeeder.json_helpers import dump_to_file_as_json

client = boto3.client("s3")
path_prefix = "tests/aws_s3/fixtures"


def generate_list_object_paginator(bucket: str, prefix: str) -> List[Any]:
    paginator = client.get_paginator("list_objects_v2")
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html?highlight=buckets#S3.Paginator.ListObjects
    pagination_config = {"MaxItems": 10, "PageSize": 2}
    page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix, PaginationConfig=pagination_config)
    all_pages = list(page_iterator)
    return all_pages


def dump_head_object():
    response = client.head_object(
        Bucket="hummingbot-mysql-archive",
        Key="parrot/Production/BinanceUserOrderModel/2020-03-12T00:00:00+00:00__2020-03-13T00:00:00+00:00.sqlite",
    )
    dump_to_file_as_json(response, os.path.join(path_prefix, "head_object.json"))


def dump_bucket_listings():
    # Note: run `aws-mfa` prior, to refresh access token

    # This should obtain listing of an existing bucket with files
    pages = generate_list_object_paginator("hummingbot-mysql-archive", "")
    dump_to_file_as_json(pages, os.path.join(path_prefix, "valid_objects_list.json"))

    # This should obtain listing from an existing bucket but with non-existent prefix
    pages = generate_list_object_paginator("hummingbot-mysql-archive", "nonexistent")
    dump_to_file_as_json(pages, os.path.join(path_prefix, "nonexistent_prefix.json"))


if __name__ == "__main__":
    dump_head_object()
    dump_bucket_listings()
