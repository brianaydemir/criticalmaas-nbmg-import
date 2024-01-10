"""
Environment variables and related functions used throughout the import process.
"""

import os
import pathlib
from typing import Union

import dotenv

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
