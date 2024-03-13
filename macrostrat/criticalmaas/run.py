"""
Integrate maps into Macrostrat.
"""

import argparse
import hashlib
import json
import logging
import pathlib
import re
import shutil
import sqlite3
import subprocess
import sys
import zipfile
from typing import Any, Optional

import magic
import minio
import psycopg
import requests

from macrostrat.criticalmaas import config
from macrostrat.criticalmaas.api import IngestAPI
from macrostrat.criticalmaas.types import MacrostratObject

API = IngestAPI(config.API_BASE_URL, config.API_TOKEN)


class UserError(RuntimeError):
    """
    A runtime error where a stack trace should not be necessary.
    """


# --------------------------------------------------------------------------


def append_line(file: Optional[pathlib.Path], data: Any) -> None:
    if file:
        with open(file, mode="a", encoding="utf-8") as fp:
            print(data, file=fp)


def get_macrostrat_objects(file: Optional[pathlib.Path]) -> list[MacrostratObject]:
    objs: list[MacrostratObject] = []

    if file:
        with open(file, mode="r", encoding="utf-8") as fp:
            while line := fp.readline():
                objs.append(MacrostratObject(**json.loads(line)))

    return objs


def get_macrostrat_object_ids(obj: MacrostratObject) -> Optional[tuple[int, int]]:
    """
    Determine the ID and associated group ID of the object.
    """
    # FIXME: Use an API endpoint for this query.
    with psycopg.connect(config.PG_DATABASE) as conn:
        record = conn.execute(
            """
            SELECT id, object_group_id
            FROM storage.object
            WHERE scheme = %s
              AND host = %s
              AND bucket = %s
              AND key = %s
            """,
            (obj.scheme, obj.host, obj.bucket, obj.key),
        ).fetchone()
    return record


def get_macrostrat_process_id(obj: MacrostratObject) -> Optional[int]:
    """
    Determine the ingest process ID of the object.
    """
    process_id = None
    ids = get_macrostrat_object_ids(obj)

    if object_group_id := ids[1] if ids else None:
        # FIXME: Use an API endpoint for this query.
        with psycopg.connect(config.PG_DATABASE) as conn:
            record = conn.execute(
                """
                SELECT id
                FROM ingest_process
                WHERE object_group_id = %s
                """,
                (object_group_id,),
            ).fetchone()
        process_id = record[0] if record else None

    return process_id


def get_macrostrat_source_id(slug: str) -> Optional[int]:
    """
    Determine the source ID for the given "slug".
    """
    # FIXME: Use an API endpoint for this query.
    with psycopg.connect(config.PG_DATABASE) as conn:
        record = conn.execute(
            """
            SELECT source_id
            FROM maps.sources
            WHERE slug = %s
            """,
            (slug,),
        ).fetchone()
    return record[0] if record else None


def is_object_completed(obj: MacrostratObject) -> bool:
    """
    Determine whether the object has been fully ingested.
    """
    process_id = get_macrostrat_process_id(obj)
    return bool(process_id and is_process_completed(process_id))


def is_process_completed(id_: int) -> bool:
    """
    Determine whether the ingest process ID has been marked as "completed."
    """
    return bool(API.get_ingest_process(id_)["state"] == "ingested")


def mark_process_as_completed(id_: int, source_id: int) -> None:
    """
    Mark the ingest process ID as "completed".
    """
    API.update_ingest_process(id_, state="ingested", source_id=source_id)


# --------------------------------------------------------------------------


def download_from_origin(obj: MacrostratObject) -> None:
    """
    Download the object from its origin.
    """
    obj.local_file.parent.mkdir(parents=True, exist_ok=True)

    logging.debug("Downloading %s to %s", obj.origin, obj.local_file)

    response = requests.get(obj.origin, stream=True, timeout=config.TIMEOUT)
    response.raise_for_status()

    with open(obj.local_file, mode="wb") as fp:
        for chunk in response.iter_content(chunk_size=config.CHUNK_SIZE):
            fp.write(chunk)


def upload_to_s3(obj: MacrostratObject) -> None:
    """
    Upload an object's local file to the object store.
    """
    s3 = minio.Minio(
        obj.host,
        access_key=config.S3_ACCESS_KEY,
        secret_key=config.S3_SECRET_KEY,
    )

    logging.debug("Uploading %s to S3 (%s/%s)", obj.local_file, obj.bucket, obj.key)
    s3.fput_object(obj.bucket, obj.key, str(obj.local_file))


def register_in_macrostrat(obj: MacrostratObject) -> None:
    """
    Register an object in Macrostrat.
    """
    mime_type = magic.Magic(mime=True).from_file(obj.local_file)
    hasher = hashlib.sha256()
    with open(obj.local_file, mode="rb") as fp:
        while data := fp.read(config.CHUNK_SIZE):
            hasher.update(data)
    sha256_hash = hasher.hexdigest()

    # Create the "ingest process".

    response = API.create_ingest_process()
    logging.debug("Resulting ingest process ID: %s", response["id"])
    object_group_id = response["object_group_id"]

    # Create the entry in the `objects` table.

    payload = {
        "scheme": obj.scheme,
        "host": obj.host,
        "bucket": obj.bucket,
        "key": obj.key,
        "source": obj.description,
        "mime_type": mime_type,
        "sha256_hash": sha256_hash,
        #
        "object_group_id": object_group_id,
    }

    logging.debug("Payload for objects API: %s", payload)
    ids = get_macrostrat_object_ids(obj)
    if object_id := ids[0] if ids else None:
        response = API.update_object(object_id, **payload)
    else:
        response = API.create_object(**payload)
    object_id = response["id"]
    logging.debug("Resulting object ID: %s", object_id)


def integrate_into_macrostrat(obj: MacrostratObject, slug_prefix: str) -> None:
    """
    Process the given object through Macrostrat's map ingestion pipeline.
    """

    #
    # Check whether this object thas already been integrated.
    #

    process_id = get_macrostrat_process_id(obj)

    if not process_id:
        raise RuntimeError(f"Object has not been fully registered: {obj}")

    if is_process_completed(process_id):
        logging.debug("Object has already been processed: %s", obj)
        return

    #
    # Determine what to ingest from the local file.
    #

    shapefiles = None

    if obj.local_file.name.endswith(".zip"):
        extracted_zip_dir = obj.local_file.parent / (obj.local_file.name + "-extracted")
        shutil.rmtree(extracted_zip_dir, ignore_errors=True)

        logging.debug("Extracting %s into %s", obj.local_file, extracted_zip_dir)

        with zipfile.ZipFile(obj.local_file) as zf:
            zf.extractall(path=extracted_zip_dir)
        shapefiles = [str(p) for p in extracted_zip_dir.glob("**/*.shp")]

    elif obj.local_file.name.endswith(".gpkg"):
        # FIXME: Do not assume that the geopackage works as-is.
        shapefiles = [str(obj.local_file)]

        #
        # NOTE: The mangling below is specific to TA1's hackathon output.
        #

        # mangled_gpkg = str(obj.local_file) + ".new.sqlite"

        # shutil.copy(obj.local_file, mangled_gpkg)

        # with sqlite3.connect(mangled_gpkg) as con:
        #     for row in con.execute("SELECT table_name FROM gpkg_contents"):
        #         table_name = row[0]
        #         label = " ".join(table_name.split("_")[2:-1])
        #         print(row, label)

        #         e_table_name = table_name.replace('"', '""')

        #         con.enable_load_extension(True)
        #         con.execute('SELECT load_extension("mod_spatialite");')
        #         con.execute(f'ALTER TABLE "{e_table_name}" ADD label TEXT')
        #         con.execute(f'UPDATE "{e_table_name}" SET label = ?', (label,))
        #         con.commit()

        # shapefiles = [mangled_gpkg]

    if shapefiles:
        #
        # Assuming the object's local filename is unique(-ish), use it
        # to generate a unique source ID for the ingestion scripts.
        #

        slug_suffix = re.sub(r"\W", "_", obj.local_file.name, flags=re.ASCII)
        slug = f"{slug_prefix}_{slug_suffix}".lower()

        logging.debug("Using %s as the slug", slug)
        logging.debug("Processing files: %s", shapefiles)

        subprocess.run(
            ["macrostrat-maps", "ingest", slug, *shapefiles],
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=True,
        )
        subprocess.run(
            ["macrostrat-maps", "prepare-fields", slug],
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=True,
        )

        source_id = get_macrostrat_source_id(slug)
        if not source_id:
            raise RuntimeError("Failed to determine source_id")

        logging.debug("Using %s as the source_id", source_id)

        subprocess.run(
            ["macrostrat-maps", "create-rgeom", str(source_id)],
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=True,
        )
        subprocess.run(
            ["macrostrat-maps", "create-webgeom", str(source_id)],
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=True,
        )
        # FIXME: Use an API endpoint for this query.
        # FIXME: Do not hard-code the map scale.
        with psycopg.connect(config.PG_DATABASE) as conn:
            conn.execute(
                """
                UPDATE maps.sources
                SET name = %s, scale = 'large'
                WHERE source_id = %s
                """,
                (obj.name, source_id),
            )
        mark_process_as_completed(process_id, source_id)


# --------------------------------------------------------------------------


def download_cli(args: argparse.Namespace) -> None:
    objs = get_macrostrat_objects(args.input)
    for obj in objs:
        try:
            download_from_origin(obj)
        except requests.RequestException:
            logging.exception("Failed to download %s", obj)
            append_line(args.error, obj)
        else:
            append_line(args.output, obj)


def register_cli(args: argparse.Namespace) -> None:
    objs = get_macrostrat_objects(args.input)
    for obj in objs:
        try:
            upload_to_s3(obj)
            register_in_macrostrat(obj)
        except Exception:  # FIXME: Catch a more specific exception type
            logging.exception("Failed to register %s", obj)
            append_line(args.error, obj)
        else:
            append_line(args.output, obj)


def integrate_cli(args: argparse.Namespace) -> None:
    objs = get_macrostrat_objects(args.input)
    for obj in objs:
        try:
            integrate_into_macrostrat(obj, args.source_id_prefix)
        except Exception:  # FIXME: Catch a more specific exception type
            logging.exception("Failed to integrate %s", obj)
            append_line(args.error, obj)
        else:
            if is_object_completed(obj):
                append_line(args.output, obj)
            else:
                append_line(args.error, obj)


# --------------------------------------------------------------------------


def init_logging() -> None:
    logging.basicConfig(
        format="[%(asctime)s] %(levelname)s %(message)s",
        level=logging.ERROR,
        stream=sys.stderr,
    )


def add_standard_io_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-i", "--input", type=pathlib.Path)
    parser.add_argument("-o", "--output", type=pathlib.Path)
    parser.add_argument("-e", "--error", type=pathlib.Path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.set_defaults(func=None)
    parser.set_defaults(verbose=False)

    subparsers = parser.add_subparsers()

    download_parser = subparsers.add_parser("download")
    download_parser.set_defaults(func=download_cli)
    add_standard_io_args(download_parser)

    register_parser = subparsers.add_parser("register")
    register_parser.set_defaults(func=register_cli)
    add_standard_io_args(register_parser)

    integrate_parser = subparsers.add_parser("integrate")
    integrate_parser.add_argument("source_id_prefix")
    integrate_parser.set_defaults(func=integrate_cli)
    add_standard_io_args(integrate_parser)

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    for path in [args.output, args.error]:
        if path and path.exists():
            with open(path, mode="w", encoding="utf-8"):
                pass  # ensure that the existing file is truncated

    if args.func:
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        args.func(args)
    else:
        raise UserError("No action specified on the command line")


def entrypoint() -> None:
    try:
        init_logging()
        main()
    except UserError as exn:
        print("ERROR:", *exn.args)
        sys.exit(1)
    except Exception:  # pylint: disable=broad-except
        logging.exception("Uncaught exception")
        sys.exit(1)


if __name__ == "__main__":
    entrypoint()
