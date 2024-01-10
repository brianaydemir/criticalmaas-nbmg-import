"""
Register one or more files in Macrostrat.
"""

import hashlib
import logging
import mimetypes
import os
import pathlib
import sys
from typing import Optional, Union

import dotenv
import minio
import psycopg
import requests

dotenv.load_dotenv()

API_BASE_URL = os.environ.get("API_BASE_URL", "API_BASE_URL not defined")
API_TOKEN = os.environ.get("API_TOKEN", "API_TOKEN not defined")
DB_CONN_URL = os.environ.get("DB_CONN_URL", "DB_CONN_URL not defined")
S3_HOST = os.environ.get("S3_HOST", "S3_HOST not defined")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "S3_ACCESS_KEY not defined")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "S3_SECRET_KEY not defined")
S3_BUCKET = os.environ.get("S3_BUCKET", "S3_BUCKET not defined")
S3_PREFIX = os.environ.get("S3_PREFIX", "S3_PREFIX not defined")


def get_scheme() -> str:
    """
    Returns the "scheme" value to use for the object registration API.
    """
    return "s3"


def get_host() -> str:
    """
    Returns the "host" value to use for the object registration API.
    """
    return S3_HOST


def get_bucket() -> str:
    """
    Returns the "bucket" value to use for the object registration API.
    """
    return S3_BUCKET


def get_key(file: Union[str, os.PathLike]) -> str:
    """
    Returns the "key" value to use for the object registration API.
    """
    return f"{S3_PREFIX}/{pathlib.Path(file).name}"


def get_macrostrat_file_id(file: Union[str, os.PathLike]) -> Optional[int]:
    """
    Returns the unique ID of the file if it has already been registered.
    """
    with psycopg.connect(DB_CONN_URL) as conn:
        record = conn.execute(
            """
            SELECT id
            FROM objects
            WHERE scheme = %s
              AND host = %s
              AND bucket = %s
              AND key = %s
            """,
            (get_scheme(), get_host(), get_bucket(), get_key(file)),
        ).fetchone()
    return record[0] if record else None


def upload_file(file: Union[str, os.PathLike]) -> None:
    """
    Uploads the file to the object store.
    """
    s3 = minio.Minio(S3_HOST, access_key=S3_ACCESS_KEY, secret_key=S3_SECRET_KEY)
    bucket_name = get_bucket()
    object_name = get_key(file)

    logging.debug("Uploading to S3: %s/%s", bucket_name, object_name)
    s3.fput_object(bucket_name, object_name, str(file))


def register_file(file: Union[str, os.PathLike]) -> None:
    """
    Registers the file in Macrostrat.

    Updates the existing entry if the file has already been registered.
    """
    mime_type = mimetypes.guess_type(file)[0]
    hasher = hashlib.sha256()
    with open(file, mode="rb") as fp:
        data = fp.read(8 * 1024 * 1024)  # 8 MB
        while data:
            hasher.update(data)
            data = fp.read(8 * 1024 * 1024)  # 8 MB
    sha256_hash = hasher.hexdigest()

    if file_id := get_macrostrat_file_id(file):
        api_op = requests.patch
        endpoint = f"/object/{file_id}"
    else:
        api_op = requests.post
        endpoint = "/object/"

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
    }
    payload = {
        "scheme": get_scheme(),
        "host": get_host(),
        "bucket": get_bucket(),
        "key": get_key(file),
        "source": {"website": "https://nbmg.unr.edu/USGS.html"},
        "mime_type": mime_type,
        "sha256_hash": sha256_hash,
    }

    logging.debug("Payload for objects API: %s", payload)
    r = api_op(f"{API_BASE_URL}{endpoint}", headers=headers, json=payload)
    r.raise_for_status()


def main() -> None:
    for file in sys.argv[1:]:
        logging.info("Processing: %s", file)
        upload_file(file)
        register_file(file)


def entrypoint() -> None:
    try:
        logging.basicConfig(
            format="%(asctime)s ~ %(message)s",
            level=logging.DEBUG,
        )
        main()
    except Exception:  # pylint: disable=broad-except
        logging.exception("Uncaught exception")
        sys.exit(1)


if __name__ == "__main__":
    entrypoint()
