"""
Settings that define the ingestion process.
"""

import pathlib

from macrostrat.core.config import settings  # type: ignore[import-untyped]

CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB
DOWNLOAD_DIR = pathlib.Path("./tmp")  # where to put downloaded objects
TIMEOUT = 10  # seconds

API_BASE_URL = settings.api_base_url
API_TOKEN = settings.api_token
PG_DATABASE = settings.pg_database
S3_HOST = settings.s3_host
S3_ACCESS_KEY = settings.s3_access_key
S3_SECRET_KEY = settings.s3_secret_key
S3_BUCKET = settings.s3_bucket
S3_PREFIX = settings.s3_prefix
