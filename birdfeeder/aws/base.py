import logging
import os
import threading
from typing import Any, Dict, Optional

import boto3
from botocore.client import BaseClient
from botocore.paginate import PageIterator

log = logging.getLogger(__name__)


class AwsBase:
    _service: str

    def __init__(  # type: ignore
        self,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        region_name: Optional[str] = None,
        **kwargs
    ) -> None:  # type: ignore

        if (access_key is not None) ^ (secret_key is not None):
            raise ValueError("You must specify both `access_key` and `secret_key` or neither of them")

        self._region_name = None
        if region_name is None and os.getenv("AWS_DEFAULT_REGION") is None:
            # Backward compatibility
            self._region_name = "us-west-2"
        else:
            self._region_name = region_name

        self._access_key = access_key
        self._secret_key = secret_key
        self._kwargs = kwargs
        self._client: Optional[BaseClient] = None
        self._client_creation_lock = threading.Lock()

    @property
    def client(self) -> BaseClient:
        # Unfortunately creation of boto3 client is NOT thread-safe
        with self._client_creation_lock:
            if not self._client:
                self._client = boto3.client(
                    self._service,
                    aws_access_key_id=self._access_key,
                    aws_secret_access_key=self._secret_key,
                    region_name=self._region_name,
                    **self._kwargs
                )
        return self._client

    def _get_page_iterator(self, command: str, operation_params: Dict[str, Any]) -> PageIterator:
        """
        Obtain page iterator for an operation.

        Mostly needed to mock API responses from unittests.
        """
        paginator = self.client.get_paginator(command)
        return paginator.paginate(**operation_params)
