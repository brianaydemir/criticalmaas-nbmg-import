"""
Look for maps in one of Macrostrat's buckets.
"""

import datetime
import hashlib
import os.path
import re
import sys
import urllib.parse
from typing import Optional

import bs4
import minio
import requests

from macrostrat.map_ingestion import config
from macrostrat.map_ingestion.types import MacrostratObject


def new_obj(bucket: str, key: str) -> MacrostratObject:
    s3 = minio.Minio(
        config.S3_HOST,
        access_key=config.S3_ACCESS_KEY,
        secret_key=config.S3_SECRET_KEY,
    )
    origin = s3.presigned_get_object(
        bucket,
        key,
        expires=datetime.timedelta(days=7),
    )

    description = {
        "event": "CriticalMAAS 6-month Hackathon",
        "url": origin,
    }

    # Construct a short but unique "basename" for the object.
    filename = urllib.parse.urlparse(origin).path.split("/")[-1]
    (root, ext) = os.path.splitext(filename)
    digest = hashlib.sha256(origin.encode("utf-8")).hexdigest()
    basename = f"{root}-{digest[:8]}{ext}"

    return MacrostratObject(
        origin=origin,
        description=description,
        #
        scheme="s3",
        host=config.S3_HOST,
        bucket=config.S3_BUCKET,
        key=f"{config.S3_PREFIX}/{basename}",
        #
        local_file=config.DOWNLOAD_DIR / basename,
        #
        name=f"CriticalMAAS 6-month Hackathon: {key}",
    )


def main() -> None:
    """
    Look for GeoPackages in one of Macrostrat's buckets.
    """

    bucket = sys.argv[1]
    prefix = sys.argv[2]

    s3 = minio.Minio(
        config.S3_HOST,
        access_key=config.S3_ACCESS_KEY,
        secret_key=config.S3_SECRET_KEY,
    )

    for obj in s3.list_objects(bucket, prefix=prefix, recursive=True):
        if obj.object_name.endswith(".gpkg"):
            print(new_obj(obj.bucket_name, obj.object_name))


if __name__ == "__main__":
    main()
