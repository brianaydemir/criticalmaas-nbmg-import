"""
Register one or more objects in Macrostrat.
"""

import hashlib
import logging
import mimetypes
import os
import sys
from typing import Optional, Union

import minio
import psycopg
import requests

from macrostrat.nbmg_import import utils


def get_macrostrat_file_id(file: Union[str, os.PathLike]) -> Optional[int]:
    """
    Returns the unique ID of the file if it has already been registered.
    """
    with psycopg.connect(utils.DB_CONN_URL) as conn:
        record = conn.execute(
            """
            SELECT id
            FROM objects
            WHERE scheme = %s
              AND host = %s
              AND bucket = %s
              AND key = %s
            """,
            (utils.get_scheme(), utils.get_host(), utils.get_bucket(), utils.get_key(file)),
        ).fetchone()
    return record[0] if record else None


def upload_file(file: Union[str, os.PathLike]) -> None:
    """
    Uploads the file to the object store.
    """
    s3 = minio.Minio(
        utils.S3_HOST,
        access_key=utils.S3_ACCESS_KEY,
        secret_key=utils.S3_SECRET_KEY,
    )
    bucket_name = utils.get_bucket()
    object_name = utils.get_key(file)

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
        "Authorization": f"Bearer {utils.API_TOKEN}",
    }
    payload = {
        "scheme": utils.get_scheme(),
        "host": utils.get_host(),
        "bucket": utils.get_bucket(),
        "key": utils.get_key(file),
        "source": {"website": "https://nbmg.unr.edu/USGS.html"},
        "mime_type": mime_type,
        "sha256_hash": sha256_hash,
    }

    logging.debug("Payload for objects API: %s", payload)
    r = api_op(f"{utils.API_BASE_URL}{endpoint}", headers=headers, json=payload)
    r.raise_for_status()


def main() -> None:
    for file in sys.argv[1:]:
        logging.info("Registering: %s", file)
        upload_file(file)
        register_file(file)


def entrypoint() -> None:
    try:
        logging.basicConfig(
            format="[%(asctime)s] %(levelname)s %(module)s:%(lineno)d %(message)s",
            level=logging.DEBUG,
        )
        main()
    except Exception:  # pylint: disable=broad-except
        logging.exception("Uncaught exception")
        sys.exit(1)


if __name__ == "__main__":
    entrypoint()
