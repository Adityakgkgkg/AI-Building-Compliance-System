"""
MCRDSE Module 1 – IFC Parser Utilities
======================================
Utility functions for resolving upload paths, generating UUIDs, and measuring
execution timing.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.parser.exceptions import IFCFileNotFoundError

_UPLOADS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "uploads"


def get_uploads_dir() -> Path:
    """Ensure and return the uploads directory path."""
    _UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    return _UPLOADS_DIR


def resolve_ifc_path(ifc_file: str | Path) -> Path:
    """
    Resolve filename or path string to an absolute Path object.
    Checks:
    1. Direct file path if it exists.
    2. Within backend/data/uploads/ directory.
    3. Within backend root directory.

    Raises
    ------
    IFCFileNotFoundError
        If file does not exist in any of the candidate locations.
    """
    path_obj = Path(ifc_file)

    # 1. Direct path check
    if path_obj.is_absolute() and path_obj.exists() and path_obj.is_file():
        return path_obj

    # 2. Uploads dir check
    upload_target = get_uploads_dir() / path_obj.name
    if upload_target.exists() and upload_target.is_file():
        return upload_target

    # 3. Relative path from CWD or backend dir
    cwd_target = Path.cwd() / path_obj
    if cwd_target.exists() and cwd_target.is_file():
        return cwd_target

    # 4. Check if filename exists anywhere inside uploads or temp
    for candidate in get_uploads_dir().glob(f"*{path_obj.name}*"):
        if candidate.is_file():
            return candidate

    raise IFCFileNotFoundError(
        detail=f"IFC file '{ifc_file}' not found. Looked in absolute path, '{upload_target}', and '{cwd_target}'."
    )




def generate_parse_id() -> str:
    """Generate UUID4 string for parse run identifier."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def perf_start() -> float:
    """Return high-resolution monotonic start time."""
    return time.perf_counter()


def elapsed_ms(t0: float) -> float:
    """Return elapsed wall-clock time in milliseconds since t0."""
    return (time.perf_counter() - t0) * 1000.0
