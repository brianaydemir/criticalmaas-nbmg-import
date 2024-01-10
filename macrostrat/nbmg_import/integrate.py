"""
Integrate registered objects (maps) into Macrostrat.
"""

import logging
import pathlib
import shutil
import subprocess
import sys
import zipfile

import minio
import psycopg

from macrostrat.nbmg_import import utils

INTEGRATE_DIR = pathlib.Path("./tmp/integrate")  # where to put downloaded files


def get_objects_to_integrate():
    """
    Returns a list of objects that need to be integrated.
    """
    with psycopg.connect(utils.DB_CONN_URL) as conn:
        records = conn.execute(
            """
            SELECT id, scheme, host, bucket, key
            FROM objects
            WHERE scheme = %s
              AND host = %s
              AND bucket = %s
              AND key ~ %s
              AND mime_type = 'application/zip'
            """,
            (utils.get_scheme(), utils.get_host(), utils.get_bucket(), f"^{utils.S3_PREFIX}/"),
        ).fetchall()
    return records


def download_s3_object(host, bucket, key) -> pathlib.Path:
    """
    Downloads the given object, and returns the path to the local file.
    """
    INTEGRATE_DIR.mkdir(parents=True, exist_ok=True)

    filename: pathlib.Path = INTEGRATE_DIR / key.split("/")[-1]
    s3 = minio.Minio(host, access_key=utils.S3_ACCESS_KEY, secret_key=utils.S3_SECRET_KEY)
    s3.fget_object(bucket, key, str(filename))

    return filename


def integrate_object(id_, scheme, host, bucket, key) -> None:
    """
    Processes the given object through Macrostrat's map ingestion pipeline.
    """
    logging.info("Processing: %s = %s://%s/%s/%s", id_, scheme, host, bucket, key)

    filename = download_s3_object(host, bucket, key)
    extracted_zip_dir = filename.parent / (filename.name + "-extracted")
    shutil.rmtree(extracted_zip_dir, ignore_errors=True)

    with zipfile.ZipFile(filename) as zf:
        zf.extractall(path=extracted_zip_dir)

    if shapefiles := [str(p) for p in extracted_zip_dir.glob("**/*.shp")]:
        logging.debug("Processing shape files: %s", shapefiles)
        subprocess.run(
            [
                "poetry",
                "run",
                "macrostrat-maps",
                "ingest",
                "baydemir_nbmg_import_2",  # FIXME hard-coded name
                *shapefiles,
            ],
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=True,
        )


def main() -> None:
    for obj in get_objects_to_integrate():
        integrate_object(*obj)


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
