"""
Environment variables and other configuration constants.
"""

import os
import pathlib

import dotenv

CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB
DOWNLOAD_DIR = pathlib.Path("./tmp")  # where to put downloaded objects
TIMEOUT = 10  # seconds

dotenv.load_dotenv()

API_BASE_URL = os.environ.get("API_BASE_URL", "API_BASE_URL not defined")
API_TOKEN = os.environ.get("API_TOKEN", "API_TOKEN not defined")
DB_CONN_URL = os.environ.get("DB_CONN_URL", "DB_CONN_URL not defined")
S3_HOST = os.environ.get("S3_HOST", "S3_HOST not defined")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "S3_ACCESS_KEY not defined")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "S3_SECRET_KEY not defined")
S3_BUCKET = os.environ.get("S3_BUCKET", "S3_BUCKET not defined")
S3_PREFIX = os.environ.get("S3_PREFIX", "S3_PREFIX not defined")
