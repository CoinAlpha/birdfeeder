import logging
from typing import Any, Dict, List

import botocore.exceptions
import typer

from birdfeeder.aws.base import AwsBase
from birdfeeder.aws.exceptions import BucketUnavailable, MaxKeyUnavailable

log = logging.getLogger(__name__)


class AwsS3(AwsBase):
    """Convenience class to wrap AWS S3 boto3 library"s various methods."""

    _service = "s3"

    def download_with_progressbar(self, bucket: str, key: str, file_path: str):  # type: ignore
        obj_meta = self.client.head_object(Bucket=bucket, Key=key)
        size = obj_meta["ContentLength"]
        with typer.progressbar(length=size) as progress:

            def progress_updater(downloaded_size):
                progress.update(downloaded_size)

            self.client.download_file(bucket, key, file_path, Callback=progress_updater)

    def get_object(self, bucket: str, key: str):  # type: ignore
        """Get object from a bucket and return it's body."""
        response = self.client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read().decode("utf-8")

    def generate_presigned(self, bucket: str, file_name: str) -> Dict[str, Any]:
        result: Dict[str, Any] = self.client.generate_presigned_post(
            Bucket=bucket, Key=file_name, Fields={"acl": "public-read"}, Conditions=[{"acl": "public-read"}]
        )
        return result

    def upload_file(self, file_name: str, bucket: str, object_name: str):  # type: ignore
        self.client.upload_file(file_name, bucket, object_name)

    def download_file(self, bucket: str, key: str, file_path: str, enable_progressbar: bool = False):  # type: ignore
        if enable_progressbar:
            return self.download_with_progressbar(bucket, key, file_path)
        self.client.download_file(bucket, key, file_path)

    def is_bucket_exists(self, bucket: str) -> bool:
        """Check whether a bucket is exists or not (or we don't have access)."""
        try:
            self.client.head_bucket(Bucket=bucket)
        except botocore.exceptions.ClientError:
            # An error occurred (403) when calling the HeadBucket operation: Forbidden
            return False
        # Note: docs states that head_bucket() may raise S3.Client.exceptions.NoSuchBucket, but it cannot be found in
        #  source code currently, and it's unknown how to reproduce it.
        return True

    def is_key_exist(self, bucket: str, key: str) -> bool:
        """Check whether an object with key exists inside the bucket."""
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except Exception:
            return False

    def list_objects(self, bucket: str, prefix: str = "") -> List[Any]:
        operation_parameters = {"Bucket": bucket, "Prefix": prefix}
        page_iterator = self._get_page_iterator("list_objects_v2", operation_parameters)
        objects = []  # type: ignore

        for page in page_iterator:
            try:
                contents = page["Contents"]  # noqa: VNE002
                objects = objects + contents
            except KeyError:
                pass

        return objects

    def get_max_key(self, bucket: str, prefix: str = "", check_bucket: bool = True) -> str:
        """
        Get most recent key (filename) in a bucket, matching a path prefix.

        :param bucket: name of the bucket to operate
        :param prefix: path prefix
        :param check_bucket: if True, first check whether the bucket is accessible
        :raises: BucketUnavailable when requested bucket is unavailable
        :raises: MaxKeyUnavailable when there are no files matching a prefix pattern
        """
        if check_bucket and not self.is_bucket_exists(bucket):
            raise BucketUnavailable("Bucket does not exists or is unavailable")

        operation_parameters = {"Bucket": bucket, "Prefix": prefix}
        page_iterator = self._get_page_iterator("list_objects_v2", operation_parameters)
        item_with_max_key = None

        def compare_func(element):
            return element["LastModified"]

        for page in page_iterator:
            try:
                contents = sorted(page["Contents"], key=compare_func)  # noqa: VNE002
            except KeyError:
                # KeyError: 'Contents'
                # raised when requesting nonexistent prefix
                raise MaxKeyUnavailable("Requested prefix does not exists")

            current_page_max_item = contents[-1]
            if item_with_max_key:
                item_with_max_key = max(item_with_max_key, current_page_max_item, key=compare_func)
            else:
                item_with_max_key = current_page_max_item

        return item_with_max_key["Key"]  # type: ignore
