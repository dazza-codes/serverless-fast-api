from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional

from .logger import get_logger

LOGGER = get_logger(__name__)


class S3Object(NamedTuple):
    """
    :param s3_bucket: Source s3 bucket for file
    :param s3_key: Source s3 key for s3 file_path
    :param s3_region: Source s3 region for file
    """

    bucket: str
    key: str
    region: str = None

    @property
    def uri(self) -> str:
        return f"s3://{self.bucket}/{self.key}"


def parse_s3_record(s3_record: Dict) -> Optional[S3Object]:
    s3_data = s3_record.get("s3")
    return S3Object(
        bucket=s3_data.get("bucket").get("name"),
        key=s3_data.get("object").get("key"),
        region=s3_record.get("awsRegion"),
    )


def parse_s3_event(s3_event: Dict) -> List[S3Object]:
    s3_records = s3_event.get("Records")
    if s3_records is None:
        msg = "Missing s3_event['Records']"
        LOGGER.error(msg)
        raise ValueError(msg)
    return [parse_s3_record(s3) for s3 in s3_records]
