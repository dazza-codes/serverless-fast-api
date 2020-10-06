from example_app.aws_s3_event import parse_s3_event
from example_app.aws_s3_event import S3Object


def test_parse_s3_event(s3_event_json):
    s3_objects = parse_s3_event(s3_event_json)
    assert s3_objects
    assert isinstance(s3_objects, list)
    s3_obj = s3_objects[0]
    assert isinstance(s3_obj, S3Object)

    records = s3_event_json["Records"]
    assert len(records) == 1
    record = records[0]
    region = record["awsRegion"]
    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]
    assert s3_obj.bucket == bucket
    assert s3_obj.key == key
    assert s3_obj.uri == f"s3://{bucket}/{key}"
    assert s3_obj.region == region
